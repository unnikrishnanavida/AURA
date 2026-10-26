/** Typed client for the real /v1/notes API (Phase E2 contract). */
export interface Note {
  note_id: string;
  title: string;
  content: string;
  scope: string;
  created_at: string | null;
}

export interface NoteInput {
  title: string;
  content: string;
  scope?: string;
}

export class NotesClient {
  private endpoint: string;
  private apiKey: string;
  private scope: string;

  constructor(endpoint: string, apiKey = "", scope = "owner:anonymous") {
    this.endpoint = endpoint;
    this.apiKey = apiKey;
    this.scope = scope;
  }

  async list(): Promise<Note[]> {
    const data = await this.req("GET", `/v1/notes?scope=${encodeURIComponent(this.scope)}`, 200);
    return (data as { notes: Note[] }).notes ?? [];
  }

  async get(id: string): Promise<Note> {
    return (await this.req("GET", `/v1/notes/${id}`, 200)) as Note;
  }

  async create(input: NoteInput): Promise<Note> {
    return (await this.req("POST", "/v1/notes", 201, {
      ...input,
      scope: input.scope ?? this.scope,
    })) as Note;
  }

  async update(id: string, input: NoteInput): Promise<Note> {
    return (await this.req("PATCH", `/v1/notes/${id}`, 200, {
      ...input,
      scope: input.scope ?? this.scope,
    })) as Note;
  }

  async remove(id: string): Promise<boolean> {
    const data = (await this.req("DELETE", `/v1/notes/${id}`, 200)) as { deleted: boolean };
    return data.deleted === true;
  }

  private async req(method: string, path: string, expect: number, body?: unknown): Promise<unknown> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;
    const res = await fetch(`${this.endpoint}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (res.status !== expect) {
      throw new Error(`${method} ${path} failed (${res.status})`);
    }
    return res.json();
  }
}