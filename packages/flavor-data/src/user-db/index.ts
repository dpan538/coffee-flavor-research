/**
 * Local user bean library (owner, 2026-09-12): Dexie over IndexedDB, no server, no account.
 *
 *   user_beans: id, name, roast_level, process, variety, concept_ids, created_at
 *   beansAsVectors() → BeanVector[] for session.ts (projectConcepts over the bean's concept ids)
 *
 * The library is the only place user data lives; it never leaves the device.
 */
import Dexie, { type Table } from "dexie";
import { projectConcepts, type BeanVector } from "../product-vector-v1/engine";

export type UserBean = {
  id?: number;
  name: string;
  roast_level: string; // light | medium_light | medium | medium_dark | dark | very_dark | ""
  process: string; // washed | natural | anaerobic | decaf | ""
  variety: string; // one variety id, or up to 3 joined with "|"
  concept_ids: string[]; // canonical sensory.* ids from the label's tasting notes
  created_at: number;
};

export class UserBeanDatabase extends Dexie {
  user_beans!: Table<UserBean, number>;

  constructor(name = "flavorwords-user-db") {
    super(name);
    this.version(1).stores({ user_beans: "++id, name, roast_level, process, variety, created_at" });
  }
}

let shared: UserBeanDatabase | null = null;

export function userDatabase(name?: string): UserBeanDatabase {
  if (name) return new UserBeanDatabase(name);
  if (!shared) shared = new UserBeanDatabase();
  return shared;
}

export async function addBean(db: UserBeanDatabase, bean: Omit<UserBean, "id" | "created_at"> & { created_at?: number }): Promise<number> {
  if (!bean.name.trim()) throw new Error("bean needs a name");
  const conceptIds = [...new Set(bean.concept_ids.filter((id) => id.startsWith("sensory.")))];
  return db.user_beans.add({ ...bean, concept_ids: conceptIds, created_at: bean.created_at ?? Date.now() });
}

export async function listBeans(db: UserBeanDatabase): Promise<UserBean[]> {
  return db.user_beans.orderBy("created_at").reverse().toArray();
}

export async function deleteBean(db: UserBeanDatabase, id: number): Promise<void> {
  await db.user_beans.delete(id);
}

export async function clearBeans(db: UserBeanDatabase): Promise<void> {
  await db.user_beans.clear();
}

/** Vectors for session.ts: only beans with at least one canonical concept get a vector. */
export async function beansAsVectors(db: UserBeanDatabase): Promise<BeanVector[]> {
  const beans = await listBeans(db);
  return beans
    .filter((b) => b.concept_ids.length > 0)
    .map((b) => ({ id: String(b.id), label: b.name, vector: projectConcepts(b.concept_ids), source: "user" as const, conceptIds: b.concept_ids }));
}

/** Parse a label's tasting-note words into canonical concept ids through the concept tag table (zh or en). */
export function conceptIdsFromLabel(text: string, conceptTags: Record<string, { "zh-CN": string; en: string }>): string[] {
  const low = text.toLowerCase();
  const ids: string[] = [];
  for (const [concept, tags] of Object.entries(conceptTags)) {
    if ((tags["zh-CN"] && low.includes(tags["zh-CN"].toLowerCase())) || (tags.en && low.includes(tags.en.toLowerCase()))) ids.push(concept);
  }
  return ids;
}
