import {test,expect} from '@playwright/test';

test('Ayuda con hover, clic y Escape; porcentajes y limpieza de avisos',async({page})=>{
 await page.goto('/');await expect(page.getByText('SIMULACIÓN ACADÉMICA')).toHaveCount(0);await expect(page.getByText('Una herramienta para ensayar, no un monitoreo real.')).toHaveCount(0);
 await page.getByRole('button',{name:'Abrir demostración'}).click();
 const help=page.getByRole('button',{name:'Ayuda: Alimento inicial',exact:true}).first();
 await help.hover();await expect(page.getByRole('tooltip')).toContainText('cuántos kg hay');
 await help.click();await page.getByRole('heading',{name:'Comederos y aves',exact:true}).hover();await expect(page.getByRole('tooltip')).toBeVisible();
 await help.focus();await help.press('Escape');await expect(page.getByRole('tooltip')).toHaveCount(0);
 await page.getByRole('button',{name:'4 Reposición',exact:true}).click();
 await expect(page.getByLabel('Objetivo de llenado',{exact:true})).toHaveValue('100');
 await page.getByLabel('Objetivo de llenado',{exact:true}).fill('80');
 await page.getByRole('button',{name:'5 Revisar y ejecutar',exact:true}).click();
 await page.getByText('Opciones avanzadas y procedencia de parámetros',{exact:true}).click();
 const config=JSON.parse(await page.getByLabel('Configuración avanzada JSON',{exact:true}).inputValue());expect(config.target).toBe(.8);
 await page.screenshot({path:'../output/screenshots/ayudas-campos.png',fullPage:true});
});

test('Decisiones basadas en el piloto, límites y filtros',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Historial y reportes',exact:true}).click();
 const row=page.getByRole('row').filter({hasText:'Piloto sintético · 13 alternativas × 30 réplicas'});
 await row.getByRole('button',{name:'Abrir',exact:true}).click();
 await expect(page.getByRole('heading',{name:'¿Qué opción encaja en tu jornada?'})).toBeVisible();
 await page.getByLabel('Límite de desperdicio',{exact:true}).fill('2');await page.getByLabel('Límite de trabajo',{exact:true}).fill('90');
 await expect(page.locator('.decision-answer')).toContainText(/Primera opción|mantener la referencia/);
 await page.getByLabel('Filtrar opciones de decisión',{exact:true}).selectOption('factibles');
 await expect(page.locator('.decision-center tbody')).toContainText('Cumple límites');
 await page.getByLabel('Límite de trabajo',{exact:true}).fill('1');
 await expect(page.locator('.decision-answer')).toContainText('Ninguna opción cumple');
 await expect(page.locator('.decision-center').getByText('No hay opciones con este filtro.')).toBeVisible();
 await page.getByLabel('Límite de trabajo',{exact:true}).fill('90');await page.getByLabel('Filtrar opciones de decisión',{exact:true}).selectOption('todas');
 await page.getByLabel('Si hay igual continuidad, priorizar',{exact:true}).selectOption('waste');
 await expect(page.locator('.decision-answer')).toContainText('en empate, menos desperdicio');
 await page.getByLabel('Si hay igual continuidad, priorizar',{exact:true}).selectOption('work');
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../output/screenshots/decisiones.png',fullPage:true});
 await page.setViewportSize({width:768,height:1024});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
