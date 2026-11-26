"use client";

import type { ScanHistoryItem } from "../components/ScanHistoryDrawer";
import type { PredictionResponse } from "../types";

const DB_NAME = "lungray_local_history";
const DB_VERSION = 1;
const STORE_NAME = "scans";
const MAX_HISTORY_ITEMS = 20;

interface StoredScanRecord {
  id: string;
  createdAt: number;
  filename: string;
  mimeType: string;
  fileBlob: Blob;
  analyzedAt: string;
  summaryLabel: string;
  tone: ScanHistoryItem["tone"];
  prediction: PredictionResponse;
  heatmapUrl: string | null;
  heatmapHasAlpha: boolean;
  contourUrl: string | null;
  contourHasAlpha: boolean;
  inLungRatio: number | null;
  selectedHead: string;
  selectedClass: number;
  selectedDiseaseName: string;
  signedOffAt: string | null;
}

function openHistoryDb(): Promise<IDBDatabase | null> {
  if (typeof window === "undefined" || !("indexedDB" in window)) {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    try {
      const request = window.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
          store.createIndex("createdAt", "createdAt", { unique: false });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

export async function loadHistoryFromDb(): Promise<ScanHistoryItem[]> {
  const db = await openHistoryDb();
  if (!db) return [];
  return new Promise((resolve) => {
    try {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => {
        const records = (req.result as StoredScanRecord[]) || [];
        records.sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));
        const hydrated: ScanHistoryItem[] = records.slice(0, MAX_HISTORY_ITEMS).map((rec) => {
          const file = new File([rec.fileBlob], rec.filename, {
            type: rec.mimeType || rec.fileBlob.type || "image/png",
          });
          return {
            id: rec.id,
            filename: rec.filename,
            previewUrl: URL.createObjectURL(rec.fileBlob),
            analyzedAt: rec.analyzedAt,
            summaryLabel: rec.summaryLabel,
            tone: rec.tone,
            file,
            prediction: rec.prediction,
            heatmapUrl: rec.heatmapUrl,
            heatmapHasAlpha: rec.heatmapHasAlpha,
            contourUrl: rec.contourUrl,
            contourHasAlpha: rec.contourHasAlpha,
            inLungRatio: rec.inLungRatio,
            selectedHead: rec.selectedHead,
            selectedClass: rec.selectedClass,
            selectedDiseaseName: rec.selectedDiseaseName,
            signedOffAt: rec.signedOffAt,
          };
        });
        resolve(hydrated);
      };
      req.onerror = () => resolve([]);
    } catch {
      resolve([]);
    } finally {
      db.close();
    }
  });
}

export async function saveHistoryItemToDb(item: ScanHistoryItem): Promise<void> {
  const db = await openHistoryDb();
  if (!db) return;

  const createdAtMatch = /^SCAN-(\d+)$/.exec(item.id);
  const createdAt = createdAtMatch ? Number(createdAtMatch[1]) : Date.now();

  const record: StoredScanRecord = {
    id: item.id,
    createdAt,
    filename: item.filename,
    mimeType: item.file.type || "image/png",
    fileBlob: item.file,
    analyzedAt: item.analyzedAt,
    summaryLabel: item.summaryLabel,
    tone: item.tone,
    prediction: item.prediction,
    heatmapUrl: item.heatmapUrl,
    heatmapHasAlpha: item.heatmapHasAlpha,
    contourUrl: item.contourUrl,
    contourHasAlpha: item.contourHasAlpha,
    inLungRatio: item.inLungRatio,
    selectedHead: item.selectedHead,
    selectedClass: item.selectedClass,
    selectedDiseaseName: item.selectedDiseaseName,
    signedOffAt: item.signedOffAt,
  };

  return new Promise((resolve) => {
    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.put(record);

      // Prune oldest records if exceeding MAX_HISTORY_ITEMS
      const allReq = store.getAll();
      allReq.onsuccess = () => {
        const records = (allReq.result as StoredScanRecord[]) || [];
        if (records.length > MAX_HISTORY_ITEMS) {
          records.sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));
          for (const stale of records.slice(MAX_HISTORY_ITEMS)) {
            store.delete(stale.id);
          }
        }
      };

      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    } catch {
      resolve();
    } finally {
      db.close();
    }
  });
}

export async function deleteHistoryItemFromDb(id: string): Promise<void> {
  const db = await openHistoryDb();
  if (!db) return;
  return new Promise((resolve) => {
    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    } catch {
      resolve();
    } finally {
      db.close();
    }
  });
}

export async function clearHistoryDb(): Promise<void> {
  const db = await openHistoryDb();
  if (!db) return;
  return new Promise((resolve) => {
    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    } catch {
      resolve();
    } finally {
      db.close();
    }
  });
}
