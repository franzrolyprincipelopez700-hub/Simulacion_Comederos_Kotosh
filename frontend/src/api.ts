export async function api(path:string,body?:unknown,method?:string){
 const response=await fetch('/api'+path,{method:method??(body?'POST':'GET'),headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
 if(!response.ok){let info;try{info=await response.json()}catch{info={detail:'No se pudo conectar con el servidor'}};throw new Error(typeof info.detail==='string'?info.detail:JSON.stringify(info.detail));}
 return response.json();
}
export type Config=Record<string,any>;
export const labels:Record<string,string>={shortage:'Tiempo sin alimento',waste:'Alimento desperdiciado',refills:'Recargas',work:'Trabajo del responsable',availability:'Disponibilidad'};
export const units:Record<string,string>={shortage:'min/comedero',waste:'%',refills:'recargas',work:'min-persona',availability:'%'};
export const num=(x:any,d=2)=>x===null||x===undefined?'No calculable':Number(x).toLocaleString('es-PE',{maximumFractionDigits:d});
