"use client";
import { useState, useEffect } from "react";
import { api } from "../../../lib/api";
import AgnesCoverButton from "../../../components/AgnesCoverButton";
import BrandKitEditor from "../../../components/BrandKitEditor";

export default function FabricaCursoPage() {
  const [courses, setCourses] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ topic: "", course_title: "", difficulty: "iniciante", price_cents: 0, target_modules: 4, lessons_per_module: 4 });
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"cursos" | "pipeline" | "historico">("cursos");

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [c, h] = await Promise.all([api.adminListCourses(), api.getCourseFactoryHistory()]);
      setCourses(c.courses || []);
      setHistory(h.runs || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function startPipeline(e: React.FormEvent) {
    e.preventDefault();
    if (!form.topic) return alert("Topico e obrigatorio");
    try {
      const res = await api.runCourseFactory(form);
      setPipelineStatus({ task_id: res.task_id, status: "starting" });
      setActiveTab("pipeline");
      pollStatus(res.task_id);
    } catch (e: any) { alert(e.message); }
  }

  async function pollStatus(taskId: string) {
    const interval = setInterval(async () => {
      try {
        const status = await api.getCourseFactoryStatus(taskId);
        setPipelineStatus(status);
        if (status.status === "completed" || status.status === "failed") {
          clearInterval(interval);
          loadData();
        }
      } catch { clearInterval(interval); }
    }, 3000);
  }

  async function publishCourse(id: string) {
    await api.adminPublishCourse(id);
    loadData();
  }

  async function deleteCourse(id: string) {
    if (!confirm("Deletar este curso?")) return;
    await api.adminDeleteCourse(id);
    loadData();
  }

  return (
    <div className="min-h-screen p-6" style={{ background: 'var(--ink)', color: 'var(--text)' }}>
      <h1 className="text-3xl font-bold mb-6">Fabrica de Cursos</h1>

      <BrandKitEditor />

      <div className="flex gap-4 mb-6">
        {["cursos", "pipeline", "historico"].map(t => (
          <button key={t} onClick={() => setActiveTab(t as any)}
            className={`px-4 py-2 rounded-lg ${activeTab === t ? "btn-primary" : ""}`}
            style={activeTab === t ? {} : { background: 'var(--surface)' }}
          >
            {t === "cursos" ? "Cursos" : t === "pipeline" ? "Pipeline" : "Historico"}
          </button>
        ))}
      </div>

      {activeTab === "cursos" && (
        <div>
          <form onSubmit={startPipeline} className="p-4 rounded-lg mb-6 grid grid-cols-2 md:grid-cols-3 gap-4" style={{ background: 'var(--surface)' }}>
            <input placeholder="Topico do curso *" value={form.topic} onChange={e => setForm({...form, topic: e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }} />
            <input placeholder="Titulo (opcional)" value={form.course_title} onChange={e => setForm({...form, course_title: e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }} />
            <select value={form.difficulty} onChange={e => setForm({...form, difficulty: e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }}>
              <option value="iniciante">Iniciante</option>
              <option value="intermediario">Intermediario</option>
              <option value="avancado">Avancado</option>
            </select>
            <input type="number" placeholder="Preco (centavos)" value={form.price_cents} onChange={e => setForm({...form, price_cents: +e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }} />
            <input type="number" placeholder="Modulos" value={form.target_modules} onChange={e => setForm({...form, target_modules: +e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }} />
            <input type="number" placeholder="Aulas/modulo" value={form.lessons_per_module} onChange={e => setForm({...form, lessons_per_module: +e.target.value})}
              className="p-2 rounded border" style={{ background: 'var(--surface2)', borderColor: 'var(--border)' }} />
            <button type="submit" className="font-bold py-2 px-4 rounded col-span-2 md:col-span-3" style={{ background: 'var(--brand)', color: 'var(--ink)' }}>
              Gerar Curso com IA
            </button>
          </form>

          {loading ? <p>Carregando...</p> : (
            <div className="grid gap-4">
              {courses.map(c => (
                <div key={c.id} className="p-4 rounded-lg flex justify-between items-center" style={{ background: 'var(--surface)' }}>
                  <div>
                    <h3 className="font-bold">{c.title}</h3>
                    <p className="text-sm" style={{ color: 'var(--text-dim)' }}>{c.topic} | {c.total_modules} modulos | {c.total_lessons} aulas | {c.difficulty}</p>
                    <span className="text-xs px-2 py-1 rounded" style={{ background: c.status === "published" ? 'var(--success)' : 'var(--warning)', color: 'var(--ink)' }}>
                      {c.status}
                    </span>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex gap-2">
                      {c.status !== "published" && <button onClick={() => publishCourse(c.id)} className="px-3 py-1 rounded text-sm" style={{ background: 'var(--success)', color: 'var(--ink)' }}>Publicar</button>}
                      <button onClick={() => deleteCourse(c.id)} className="px-3 py-1 rounded text-sm" style={{ background: 'var(--error)', color: 'var(--ink)' }}>Deletar</button>
                    </div>
                    <AgnesCoverButton entityType="course" entityId={c.id} onDone={loadData} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "pipeline" && pipelineStatus && (
        <div className="p-6 rounded-lg" style={{ background: 'var(--surface)' }}>
          <h2 className="text-xl font-bold mb-4">Pipeline: {pipelineStatus.course_title || pipelineStatus.topic || "..."}</h2>
          <div className="mb-4">
            <span className={`px-3 py-1 rounded text-sm ${
              pipelineStatus.status === "starting" ? "animate-pulse" : ""
            }`} style={{ background: pipelineStatus.status === "completed" ? 'var(--success)' : pipelineStatus.status === "failed" ? 'var(--error)' : 'var(--warning)', color: 'var(--ink)' }}>{pipelineStatus.status}</span>
          </div>
          {pipelineStatus.macro_stages && Object.entries(pipelineStatus.macro_stages).map(([id, stage]: any) => (
            <div key={id} className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span>{id}</span>
                <span>{stage.progress}% — {stage.message}</span>
              </div>
              <div className="w-full rounded-full h-2" style={{ background: 'var(--surface2)' }}>
                <div className="h-2 rounded-full transition-all" style={{width: `${stage.progress}%`, background: stage.status === "completed" ? 'var(--success)' : stage.status === "failed" ? 'var(--error)' : 'var(--brand)'}} />
              </div>
            </div>
          ))}
          <p className="text-sm mt-4" style={{ color: 'var(--text-dim)' }}>
            Palavras: {pipelineStatus.total_words || 0} | Aulas: {pipelineStatus.total_lessons || 0}
          </p>
        </div>
      )}

      {activeTab === "pipeline" && !pipelineStatus && (
        <p style={{ color: 'var(--text-dim)' }}>Nenhuma pipeline em andamento. Inicie uma na aba Cursos.</p>
      )}

      {activeTab === "historico" && (
        <div className="grid gap-3">
          {history.map(r => (
            <div key={r.id} className="p-3 rounded flex justify-between items-center" style={{ background: 'var(--surface)' }}>
              <div>
                <span className="font-mono text-xs" style={{ color: 'var(--text-dim)' }}>{r.id}</span>
                <span className="ml-2 text-sm">{r.phase} — {r.total_lessons_generated} aulas</span>
              </div>
              <span className="text-xs px-2 py-1 rounded" style={{ background: r.status === "completed" ? 'var(--success)' : r.status === "failed" ? 'var(--error)' : 'var(--warning)', color: 'var(--ink)' }}>
                {r.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
