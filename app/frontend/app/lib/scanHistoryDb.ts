"use client";

import type { ScanHistoryItem } from "../components/ScanHistoryDrawer";

const DB_NAME = "lungray_local_history";
const STORE_NAME = "scans";
export const MAX_HISTORY_ITEMS = 20;
type StoredScanRecord = Omit<ScanHistoryItem, "previewUrl" | "file"> & {
  createdAt: number; mimeType: string; fileBlob: Blob;
};

export function createScanPreview(file: Blob): string { return URL.createObjectURL(file); }

export function patchScanHistory(items: ScanHistoryItem[], id: string, patch: Partial<ScanHistoryItem>): ScanHistoryItem[] {
  return items.map(item => item.id === id ? { ...item, ...patch } : item);
}

export function releaseHistoryPreviews(items: ScanHistoryItem[]): void {
  items.forEach(item => URL.revokeObjectURL(item.previewUrl));
}

function openHistoryDb(): Promise<IDBDatabase | null> {
  return new Promise(resolve => {
    let settled = false;
    const finish = (db: IDBDatabase | null) => {
      if (settled) { db?.close(); return; }
      settled = true; clearTimeout(timer); resolve(db);
    };
    const timer = setTimeout(() => finish(null), 2500);
    try {
      if (typeof window === "undefined" || !window.indexedDB) { finish(null); return; }
      const request = window.indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: "id" }).createIndex("createdAt", "createdAt");
        }
      };
      request.onsuccess = () => {
        request.result.onversionchange = () => request.result.close();
        finish(request.result);
      };
      request.onerror = request.onblocked = () => finish(null);
    } catch { finish(null); } // Includes private-mode getters and open() exceptions.
  });
}

async function transact<T>(mode: IDBTransactionMode, fallback: T,
  work: (store: IDBObjectStore, result: (value: T) => void) => void): Promise<T> {
  const db = await openHistoryDb();
  if (!db) return fallback;
  return new Promise(resolve => {
    let value = fallback;
    try {
      const tx = db.transaction(STORE_NAME, mode);
      tx.oncomplete = () => { db.close(); resolve(value); };
      tx.onabort = () => { db.close(); resolve(fallback); };
      tx.onerror = () => { /* Default IndexedDB behavior aborts the transaction. */ };
      try { work(tx.objectStore(STORE_NAME), next => { value = next; }); }
      catch { tx.abort(); }
    } catch { db.close(); resolve(fallback); }
  });
}

function newestFirst(a: StoredScanRecord, b: StoredScanRecord): number {
  return (Number(b.createdAt) || 0) - (Number(a.createdAt) || 0) || a.id.localeCompare(b.id);
}

export async function loadHistoryFromDb(): Promise<ScanHistoryItem[]> {
  const records = await transact<StoredScanRecord[]>("readonly", [], (store, result) => {
    const req = store.getAll();
    req.onsuccess = () => result(req.result);
  });
  const hydrated: ScanHistoryItem[] = [];
  for (const record of records.sort(newestFirst).slice(0, MAX_HISTORY_ITEMS)) {
    try {
      const { fileBlob, mimeType, ...metadata } = record;
      const file = new File([fileBlob], record.filename, { type: mimeType || "image/png" });
      hydrated.push({ ...metadata, file, previewUrl: createScanPreview(fileBlob) });
    } catch { /* A malformed legacy record must not break the drawer. */ }
  }
  return hydrated;
}

// Keep writes/deletes/clear in invocation order, even when opening the DB is slow.
let pendingWrite: Promise<unknown> = Promise.resolve();
function enqueueWrite(work: () => Promise<boolean>): Promise<boolean> {
  const next = pendingWrite.then(work, work);
  pendingWrite = next.catch(() => false);
  return next;
}

export function saveHistoryItemToDb(item: ScanHistoryItem): Promise<boolean> {
  return enqueueWrite(() => transact("readwrite", false, (store, result) => {
    const { file, previewUrl, ...metadata } = item;
    void previewUrl;
    const match = /^SCAN-(\d+)(?:-|$)/.exec(item.id);
    const record: StoredScanRecord = { ...metadata, fileBlob: file,
      mimeType: file.type, createdAt: item.createdAt ?? (match ? Number(match[1]) : Date.now()) };
    store.put(record);
    const request = store.getAll();
    request.onsuccess = () => {
      for (const old of (request.result as StoredScanRecord[]).sort(newestFirst).slice(MAX_HISTORY_ITEMS)) store.delete(old.id);
      result(true);
    };
  }));
}

export function deleteHistoryItemFromDb(id: string): Promise<boolean> {
  return enqueueWrite(() => transact("readwrite", false, (store, result) => {
    store.delete(id); result(true);
  }));
}
export function clearHistoryDb(): Promise<boolean> {
  return enqueueWrite(() => transact("readwrite", false, (store, result) => {
    store.clear(); result(true);
  }));
}
