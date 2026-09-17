// Keep a take until the server acknowledges it, scoped to the signed-in user and question.
export type SavedTake = {
  key: string;
  blob: Blob;
  duration: number;
  updated: number;
};
async function database() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("vstep-speaking-recordings", 1);
    request.onupgradeneeded = () =>
      request.result.createObjectStore("takes", { keyPath: "key" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
export async function saveTake(take: SavedTake) {
  const db = await database();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("takes", "readwrite");
      tx.objectStore("takes").put(take);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}
export async function loadTake(key: string): Promise<SavedTake | null> {
  const db = await database();
  try {
    return await new Promise((resolve, reject) => {
      const req = db.transaction("takes").objectStore("takes").get(key);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  } finally {
    db.close();
  }
}
export async function removeTake(key: string) {
  const db = await database();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction("takes", "readwrite");
      tx.objectStore("takes").delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}
