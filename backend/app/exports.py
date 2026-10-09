import io,csv,json
from xml.sax.saxutils import escape
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

LABELS={'shortage':'Tiempo sin alimento (min/comedero)','waste':'Alimento desperdiciado (%)','refills':'Recargas (número)','work':'Trabajo del responsable (min-persona)','availability':'Disponibilidad (%)'}
def safe(v):
    # Prevent formula injection in files opened in spreadsheet applications.
    if isinstance(v,str) and v[:1] in ('=','+','-','@'): return "'"+v
    return v
def generate(job,rows,format,series):
    buf=io.BytesIO()
    flat=[{'alternativa':r['alternative'],'réplica':r['replicate'],'semilla':r['result']['seed'],**r['result']['metrics']} for r in rows]
    if format=='csv':
        text=io.StringIO(); w=csv.DictWriter(text,fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)
        return text.getvalue().encode('utf-8-sig'),'text/csv'
    if format=='xlsx':
        configs=[{'alternativa':i,'parámetro':k,'valor':safe(json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else str(v))} for i,c in enumerate(job.payload['configurations']) for k,v in c.items()]
        summary=[{'alternativa':s['name'],'indicador':LABELS[m],**v} for s in job.summary['summaries'] for m,v in s['metrics'].items()]
        comps=[{'alternativa':r['alternative'],'indicador':r['metric'],**r['difference'],'p':r['p'],'p_Holm':r.get('p_holm')} for r in job.summary['comparisons']]
        with pd.ExcelWriter(buf,engine='openpyxl') as writer:
            for name,data in [('Configuración',configs),('Réplicas',flat),('Resumen',summary),('Comparaciones',comps),('Trazabilidad',[{'modelo':'1.0.0','fecha':job.created.isoformat(),'nombre':safe(job.name),'exploratorio':job.payload['exploratory']}])]:
                pd.DataFrame(data).map(safe).to_excel(writer,sheet_name=name,index=False)
                ws=writer.sheets[name]; ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
                for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in col[:30])+2))
        return buf.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    styles=getSampleStyleSheet(); styles['Title'].textColor=colors.HexColor('#146b56')
    def p(text,style='BodyText'): return Paragraph(escape(str(text)),styles[style])
    story=[p('Simulador Avícola Kotosh','Title'),p(job.name,'Heading1'),p(f'Fecha: {job.created.astimezone(__import__("zoneinfo").ZoneInfo("America/Lima")).strftime("%d/%m/%Y %H:%M")} · Modelo 1.0.0'),Spacer(1,12)]
    c=job.payload['configurations'][0]
    story.extend([p(f'Origen: {c["origin"]}. Horizonte: {c["horizon"]} min. Réplicas por alternativa: {c["replicates"]}. Semilla: {c["seed"]}.'),p('Resultados exploratorios' if job.payload['exploratory'] else 'Bloque de confirmación independiente','Heading2'),p(job.summary['message'])])
    def table(data,widths=None):
        t=Table([[p(v) for v in row] for row in data],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f3ee')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#cadbd3'))])); return t
    for s in job.summary['summaries']:
        story.extend([KeepTogether([p(s['name'],'Heading2'),table([['Indicador','Media','IC de confianza']]+[[LABELS[m],f'{v["mean"]:.3f}' if v['mean'] is not None else 'No calculable',f'{v["low"]:.3f} a {v["high"]:.3f}' if v['low'] is not None else 'Requiere réplicas'] for m in LABELS for v in [s['metrics'][m]]],[250,65,170])]),Spacer(1,8)])
    config_labels={'birds':'Número de aves','demand_kg_hour':'Demanda potencial (kg/h)','horizon':'Horizonte (min)','service_start':'Inicio del servicio (min)','service_end':'Fin del servicio (min)','reserve':'Reserva inicial (kg)','mode':'Modo','step':'Paso temporal (min)','redistribution':'Redistribución entre comederos','loss_fraction':'Fracción perdida en carga','limits_origin':'Procedencia de límites'}
    story.extend([PageBreak(),p('Configuración y balance','Heading1'),table([['Parámetro','Valor']]+[[label,('Sí' if c[key] else 'No') if isinstance(c[key],bool) else str(c[key])] for key,label in config_labels.items()],[200,285])])
    story.extend([p('Comederos de la configuración de referencia','Heading2'),table([['ID','Capacidad (kg)','Inicial (kg)','Peso de demanda']]+[[f['id'],str(f['capacity']),str(f['initial']),str(f['weight'])] for f in c['feeders']],[80,135,135,135]),p('Políticas evaluadas','Heading2'),table([['Alternativa','Regla']]+[[x['name'],f'Objetivo {x["target"]*100:g}%; '+(f'horarios {x["schedule"]}, demora {x["reference_delay"]} min, máximo {x["reference_amount"]} kg' if x['policy']=='P0' else f'intervalo {x["interval"]} min'+(f', umbral {x["threshold"]*100:g}%' if x['policy']=='P2' else ''))] for x in job.payload['configurations']],[220,265]),p(f'Responsable disponible de {c["worker_start"]} a {c["worker_end"]} min. Inspección {c["inspection"]}, desplazamiento {c["travel"]}, preparación {c["preparation"]}, carga {c["loading"]} y reparación {c["repair"]} min. Variabilidad acotada: ±{c["variation"]*100:g}%. Perfil relativo de demanda: {c["demand_profile"]}. Entradas externas: {c["entries"]}. Incidencias preparadas: {c["incidents"]}.'),p(f'Límites: desperdicio {c["max_waste"] if c["max_waste"] is not None else "sin definir"}%; trabajo {c["max_work"] if c["max_work"] is not None else "sin definir"} min-persona.')])
    r=rows[0]['result']['metrics']
    story.extend([p('Balance de la primera réplica de referencia (kg)','Heading2'),p('Inicial + entradas externas = consumo + pérdidas + retiros recuperables + final. La reserva está dentro de la frontera; las recargas son transferencias internas.'),table([['Inicial','Entradas','Consumo','Pérdidas','Retiros','Final']]+[[f'{r[k]:.4f}' for k in ['initial','external','consumption','losses','recoverable','final']]],[81]*6)])
    if series:
        fig,ax=plt.subplots(figsize=(7,3.2))
        for i,f in enumerate(series[0]['feeders']): ax.step([x['time'] for x in series],[x['feeders'][i]['level'] for x in series],where='post',label=f['id'])
        ax.set(xlabel='Tiempo simulado (min)',ylabel='Alimento almacenado (kg)',title='Nivel de alimento · primera réplica de referencia'); ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
        img=io.BytesIO(); fig.savefig(img,format='png',dpi=150); plt.close(fig); img.seek(0)
        story.extend([Spacer(1,10),Image(img,width=480,height=220)])
    if job.summary['comparisons']:
        story.extend([PageBreak(),p('Diferencias emparejadas respecto a P0','Heading1'),table([['Alternativa / indicador','Diferencia media','p Holm']]+[[f'{x["alternative"]} / {LABELS[x["metric"]]}',f'{x["difference"]["mean"]:.3f}' if x['difference']['mean'] is not None else 'No calculable',('< 0.0001' if x.get('p_holm',1)<.0001 else f'{x.get("p_holm",1):.4f}') if x['p'] is not None else 'No calculable'] for x in job.summary['comparisons']],[290,95,100])])
    story.append(KeepTogether([p('Supuestos y limitaciones','Heading2'),p(job.summary['method']),p('Demanda por pasos temporales: comprobar sensibilidad de la resolución. No se estima crecimiento biológico ni se acumula demanda no atendida. Los supuestos sintéticos no son mediciones de Kotosh. Los intervalos t requieren bloques independientes y una distribución de medias/diferencias razonable; 30 réplicas no garantizan precisión. Diferencias sin variabilidad no permiten un contraste t: se muestran descriptivamente. Cierre [0,H): eventos exactamente al cierre no se completan.'),p('Procedencia declarada: '+json.dumps(c['provenance'],ensure_ascii=False))]))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',9); canvas.setFillColor(colors.HexColor('#54706a')); canvas.drawString(42,25,'Kotosh · simulación académica · datos y límites declarados'); canvas.drawRightString(550,25,str(doc.page))
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue(),'application/pdf'
