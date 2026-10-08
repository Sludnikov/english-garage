const FILE = 'progress.json';
async function handle() { const root = await navigator.storage.getDirectory(); return root.getFileHandle(FILE, {create: true}); }
self.onmessage = async event => {
  const {id, type, payload} = event.data;
  try {
    const file = await handle();
    if (type === 'read') {
      const text = await (await file.getFile()).text();
      self.postMessage({id, ok: true, data: text ? JSON.parse(text) : null});
    } else if (type === 'write') {
      const data = JSON.stringify(payload);
      if (file.createWritable) {
        const stream = await file.createWritable(); await stream.write(data); await stream.close();
      } else {
        const access = await file.createSyncAccessHandle();
        try { access.truncate(0); access.write(new TextEncoder().encode(data), {at: 0}); access.flush(); } finally { access.close(); }
      }
      self.postMessage({id, ok: true});
    }
  } catch (error) { self.postMessage({id, ok: false, error: String(error)}); }
};
