"use client";
import { useState, useEffect } from "react";
import { api } from "../../../lib/api";

export default function TrilhasPage() {
  const [paths, setPaths] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", slug: "", description: "" });
  const [selectedPath, setSelectedPath] = useState<any>(null);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([api.adminListLearningPaths(), api.adminListCourses()]);
      setPaths(p.paths || []);
      setCourses(c.courses || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function createPath(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title || !form.slug) return alert("Titulo e slug obrigatorios");
    await api.adminCreateLearningPath(form);
    setForm({ title: "", slug: "", description: "" });
    loadData();
  }

  async function deletePath(id: string) {
    if (!confirm("Deletar esta trilha?")) return;
    await api.adminDeleteLearningPath(id);
    setSelectedPath(null);
    loadData();
  }

  async function addCourseToPath(pathId: string, courseId: string) {
    const order = selectedPath?.courses?.length ? selectedPath.courses.length + 1 : 1;
    await api.adminAddCourseToPath(pathId, courseId, order);
    const updated = await api.adminGetLearningPath(pathId);
    setSelectedPath(updated.path);
    loadData();
  }

  async function removeCourseFromPath(pathId: string, courseId: string) {
    await api.adminRemoveCourseFromPath(pathId, courseId);
    const updated = await api.adminGetLearningPath(pathId);
    setSelectedPath(updated.path);
    loadData();
  }

  async function viewPath(id: string) {
    const res = await api.adminGetLearningPath(id);
    setSelectedPath(res.path);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">Trilhas de Aprendizado</h1>

      <form onSubmit={createPath} className="bg-gray-900 p-4 rounded-lg mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <input placeholder="Titulo da trilha *" value={form.title} onChange={e => setForm({...form, title: e.target.value})}
          className="bg-gray-800 p-2 rounded border border-gray-700" />
        <input placeholder="Slug (url-amigavel) *" value={form.slug} onChange={e => setForm({...form, slug: e.target.value})}
          className="bg-gray-800 p-2 rounded border border-gray-700" />
        <input placeholder="Descricao" value={form.description} onChange={e => setForm({...form, description: e.target.value})}
          className="bg-gray-800 p-2 rounded border border-gray-700" />
        <button type="submit" className="bg-amber-500 hover:bg-amber-600 text-black font-bold py-2 px-4 rounded">
          Criar Trilha
        </button>
      </form>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-bold mb-3">Trilhas ({paths.length})</h2>
          {loading ? <p>Carregando...</p> : paths.map(p => (
            <div key={p.id} className={`bg-gray-900 p-4 rounded-lg mb-3 cursor-pointer border ${selectedPath?.id === p.id ? "border-amber-500" : "border-transparent"}`}
              onClick={() => viewPath(p.id)}>
              <div className="flex justify-between">
                <div>
                  <h3 className="font-bold">{p.title}</h3>
                  <p className="text-sm text-gray-400">/{p.slug} | {p.total_courses} cursos</p>
                  <span className={`text-xs px-2 py-1 rounded ${p.status === "published" ? "bg-green-800" : "bg-yellow-800"}`}>{p.status}</span>
                </div>
                <button onClick={(e) => { e.stopPropagation(); deletePath(p.id); }} className="text-red-400 hover:text-red-300 text-sm">Deletar</button>
              </div>
            </div>
          ))}
        </div>

        <div>
          {selectedPath && (
            <div className="bg-gray-900 p-4 rounded-lg">
              <h2 className="text-xl font-bold mb-3">{selectedPath.title}</h2>
              <p className="text-sm text-gray-400 mb-4">{selectedPath.description}</p>

              <h3 className="font-bold mb-2">Cursos na Trilha ({selectedPath.courses?.length || 0})</h3>
              {selectedPath.courses?.map((c: any) => (
                <div key={c.id} className="bg-gray-800 p-2 rounded mb-2 flex justify-between items-center">
                  <span>{c.order}. {c.title}</span>
                  <button onClick={() => removeCourseFromPath(selectedPath.id, c.id)} className="text-red-400 text-sm">Remover</button>
                </div>
              ))}

              <h3 className="font-bold mt-4 mb-2">Adicionar Curso</h3>
              <div className="grid gap-2">
                {courses.filter(c => !selectedPath.courses?.some((sc: any) => sc.id === c.id)).map(c => (
                  <div key={c.id} className="bg-gray-800 p-2 rounded flex justify-between items-center">
                    <span className="text-sm">{c.title}</span>
                    <button onClick={() => addCourseToPath(selectedPath.id, c.id)} className="text-green-400 text-sm">+ Adicionar</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
