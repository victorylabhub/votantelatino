# Votante Latino (latinos.voto)

## Publicar
1. Instalar Node.js 18 o superior.
2. En esta carpeta: `npx netlify-cli login` y luego `npx netlify-cli link` (elegir el proyecto **votante-latino**).
3. `npx netlify-cli deploy --prod`
4. En Netlify → Domain management: agregar `latinos.voto`.
5. Al lanzar: Project configuration → Access & security → desactivar el inicio de sesión obligatorio del equipo.

## Señal en vivo (YouTube)
En Netlify → Environment variables agregar:
- `YT_CHANNEL_ID`: ID del canal (empieza con "UC").
- `YT_API_KEY`: clave de YouTube Data API v3 (Google Cloud Console → APIs & Services → habilitar "YouTube Data API v3" → Credentials → Create API key; restringirla a esa API).
Sin estas variables el sitio funciona; el bloque en vivo simplemente no aparece.

## Editar contenido
- Textos en español e inglés: `content.json`
- Datos generales y modo prelanzamiento: `site.json` (`"prelaunch": false` al lanzar)
- Horarios de cierre y enlaces de resultados: `data/`
- Después de editar: `pip install -r requirements.txt` (una vez) y `python3 build.py`, luego publicar.

## Revisar antes de lanzar
- Enlaces de resultados de IA, NV, PA, WV (no verificables automáticamente) y MD.
- Horarios de New Hampshire y North Dakota (fijados por cada localidad).
- Completar financiamiento y dirección editorial en "Quiénes somos".
- Aviso de privacidad: revisión jurídica.
