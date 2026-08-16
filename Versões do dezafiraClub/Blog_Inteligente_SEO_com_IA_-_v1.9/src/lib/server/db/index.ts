export interface QueryResult {
  rows: any[];
  lastInsertRowid: number;
  rowsAffected: number;
}

export async function query(sql: string, params: any[] = []): Promise<any[]> {
  return [];
}

export async function queryOne(sql: string, params: any[] = []): Promise<any | null> {
  return null;
}

export async function exec(sql: string): Promise<void> {}

export function getPool() {
  return null;
}