import {test,expect} from '@playwright/test';
test('Crear escenario, ejecutar, reproducir y exportar',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Una jornada mejor abastecida'})).toBeVisible();
 await page.getByRole('button',{name:'Abrir demostración'}).click();
 await page.getByLabel('Nombre del escenario',{exact:true}).fill('E2E · jornada sintética');
 await page.getByRole('button',{name:'5 Revisar y ejecutar'}).click();
 await page.getByRole('button',{name:'Guardar escenario'}).click();await expect(page.getByRole('status')).toContainText('guardado');
 await page.getByRole('button',{name:'Ejecutar jornada'}).click();
 await expect(page.getByRole('heading',{name:'Reproducción de eventos calculados'})).toBeVisible({timeout:45000});
 await expect(page.getByText('Balance consistente')).toBeVisible();
 await page.getByRole('button',{name:'Reproducir',exact:true}).click();await expect(page.getByRole('button',{name:'Pausar reproducción'})).toBeVisible();
 await page.getByRole('button',{name:'Pausar reproducción'}).click();
 for(const format of ['CSV','XLSX','PDF']){
  const download=page.waitForEvent('download');await page.getByRole('link',{name:format,exact:true}).click();const file=await download;expect(await file.failure()).toBeNull();
 }
 const oldRun=await page.getByLabel('Réplica para visualizar',{exact:true}).inputValue();
 await page.getByRole('button',{name:'Ejecutar confirmación con nuevas semillas'}).click();
 await expect(page.getByRole('heading',{name:'Reproducción de eventos calculados'})).toBeVisible({timeout:45000});
 const newRun=await page.getByLabel('Réplica para visualizar',{exact:true}).inputValue();expect(newRun).not.toBe(oldRun);
 const confirmed=await (await page.request.get('/api/runs/'+newRun+'/detail')).json();expect(confirmed.run.seed).toBe(102026);
 await page.getByRole('button',{name:'Historial y reportes',exact:true}).click();await expect(page.getByRole('table').first()).toContainText('E2E · jornada sintética');
});
test('Comparar alternativas y navegar datos de campo',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Comparar alternativas',exact:true}).click();
 await page.getByLabel('Réplicas por alternativa',{exact:true}).fill('2');await page.getByLabel('Intervalos P1',{exact:true}).fill('90');await page.getByLabel('Objetivos de llenado',{exact:true}).fill('100');await page.getByLabel('Umbrales P2',{exact:true}).fill('20');await page.getByLabel('Intervalos de inspección P2',{exact:true}).fill('30');
 await page.getByRole('button',{name:'Ejecutar comparación'}).click();
 await expect(page.getByRole('heading',{name:'Comparación de alternativas',exact:true})).toBeVisible({timeout:60000});
 await expect(page.getByRole('heading',{name:'¿Qué opción encaja en tu jornada?'})).toBeVisible();
 await page.getByRole('button',{name:'Datos de campo',exact:true}).click();
 await page.getByLabel('Datos de campo CSV',{exact:true}).fill('date,time,feeder,kind,kg,end_time,value,notes\nmal,08:00,C1,suministro,-2,,,\n');
 await page.getByRole('button',{name:'Revisar filas antes de incorporar'}).click();await expect(page.getByRole('alert')).toContainText('Fila 2');
 await expect(page.getByRole('button',{name:'Confirmar incorporación'})).toBeDisabled();
});
test('Diseño de escritorio y tableta',async({page})=>{
 await page.goto('/');await expect(page.getByText('Alimento disponible.')).toBeVisible();
 await page.screenshot({path:'../output/screenshots/inicio.png',fullPage:true});
 await page.setViewportSize({width:768,height:1024});await page.screenshot({path:'../output/screenshots/tableta.png',fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
