import {test,expect} from '@playwright/test';

test('guía organizada, consulta y accesos a herramientas',async({page})=>{
 await page.goto('/');
 await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('button',{name:'Guía de uso'}).click();
 await expect(page.getByRole('heading',{name:'Mantener alimento accesible, con pérdidas y trabajo controlados'})).toBeVisible();
 await expect(page.getByRole('navigation',{name:'Contenido de la guía'}).getByRole('link')).toHaveCount(8);
 await page.getByRole('link',{name:'Consultar el glosario'}).click();
 await page.getByRole('textbox',{name:'Buscar en el glosario'}).fill('replica');
 await expect(page.locator('.guide-glossary dt')).toHaveText(['Réplica']);
 await page.getByRole('textbox',{name:'Buscar en el glosario'}).fill('zzzzz');
 await expect(page.getByRole('status')).toContainText('No hay términos');
 await page.locator('#consultas summary').filter({hasText:'¿La demanda depende automáticamente'}).click();
 await expect(page.getByText('La entrada de demanda es del lote completo')).toBeVisible();
 await page.getByRole('button',{name:'Preparar alternativas'}).click();
 await expect(page.getByRole('heading',{name:'Compara maneras de reponer'})).toBeVisible();
 await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('button',{name:'Guía de uso'}).click();
 await page.getByRole('button',{name:'Configurar una jornada'}).click();
 await expect(page.getByRole('heading',{name:'Configura tu jornada'})).toBeVisible();
});

test('guía legible en escritorio y móvil sin desbordar la página',async({page})=>{
 await page.goto('/');
 await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('button',{name:'Guía de uso'}).click();
 await expect(page.locator('.guide-cover')).toBeVisible();
 await page.screenshot({path:'../output/screenshots/guide-desktop.png',fullPage:false});
 await page.setViewportSize({width:390,height:844});
 await expect(page.locator('.guide-cover')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:'../output/screenshots/guide-mobile.png',fullPage:false});
});
