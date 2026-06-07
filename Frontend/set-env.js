const fs = require('fs');
const path = require('path');

/**
 * Script robusto para generar environment.ts desde .env
 */

const envPath = path.join(__dirname, '.env');
const targetPath = path.join(__dirname, 'src/environments/environment.ts');
const targetPathProd = path.join(__dirname, 'src/environments/environment.prod.ts');

let envConfigFile = '';

if (fs.existsSync(envPath)) {
  envConfigFile = fs.readFileSync(envPath, 'utf8');
} else {
  console.error('❌ ERROR: No se encontró el archivo Frontend/.env');
  console.log('👉 Asegúrate de crear el archivo .env en la carpeta Frontend');
  process.exit(1);
}

// Función para extraer variables sin importar si tienen espacios o comillas
function getVar(name) {
  const regex = new RegExp(`${name}\\s*=\\s*["']?(.*?)["']?(\\s|$)`, 'i');
  const match = envConfigFile.match(regex);
  return match ? match[1].trim() : '';
}

const mapboxToken = getVar('MAPBOX_TOKEN');
const apiUrl = getVar('API_URL') || 'http://localhost:8000';
const apiUrlProd = getVar('API_URL_PROD') || apiUrl;

if (!mapboxToken) {
  console.warn('⚠️ ADVERTENCIA: MAPBOX_TOKEN no está definido en tu .env');
}

const content = `// ARCHIVO GENERADO AUTOMÁTICAMENTE - NO EDITAR MANUALMENTE
export const environment = {
  production: false,
  apiUrl: '${apiUrl}',
  mapboxToken: '${mapboxToken}'
};
`;

const contentProd = `// ARCHIVO GENERADO AUTOMÁTICAMENTE - NO EDITAR MANUALMENTE
export const environment = {
  production: true,
  apiUrl: '${apiUrlProd}',
  mapboxToken: '${mapboxToken}'
};
`;

fs.writeFileSync(targetPath, content);
fs.writeFileSync(targetPathProd, contentProd);

console.log('✅ Entornos actualizados correctamente:');
console.log(`   📍 API: ${apiUrl}`);
console.log(`   📍 Mapbox: ${mapboxToken.substring(0, 10)}...`);
