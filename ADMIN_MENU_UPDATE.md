# 📋 Atualização do Menu Admin — Ordem Corrigida

## Nova Ordem das Fábricas

```
Fábricas
├─ 🎯 Ofertas ← PRIMEIRO
├─ ❐ Ebook
├─ ▣ Curso
├─ ✎ Blog
├─ 🖼️ Capas Agnes
├─ 🎬 VSL
├─ 🔗 Bio Sites
├─ 📱 MiniApps
├─ 🎯 Blueprint
└─ 📦 Produtos
```

---

## Código para Adicionar no page.tsx

Abra: `club-frontend/app/admin/page.tsx`

### Passo 1: Adicionar no Array de Tabs (PRIMEIRO)

Encontre o array de tabs e adicione **no início**:

```typescript
{
  id: "fabrica-ofertas",
  label: "🎯 Ofertas",
  icon: "🎯",
  description: "Dário + Team — Investigação, Modelagem, Copy e Personagens",
  href: "/admin/fabrica-ofertas"
},
```

### Passo 2: Adicionar no Render Condicional (PRIMEIRO)

Encontre a seção de renderização e adicione **antes de todas as outras**:

```tsx
{tab === "fabrica-ofertas" && (
  <div className="bg-[#111827] rounded-2xl border border-[#1e293b] p-6">
    <div className="flex items-start justify-between">
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          🎯 Fábrica de Ofertas
        </h3>
        <p className="text-gray-400 text-sm mt-1">
          Dário + Team — Investigação, Modelagem, Copy e Personagens
        </p>
        <p className="text-gray-500 text-xs mt-2 max-w-xl">
          Crie ofertas escaláveis com investigação automática de Facebook Ads 
          (20 anúncios escalados) + Google SEO (keywords + backlinks), 
          modelagem estratégica, copywriting de alta conversão e geração 
          de personagens (2 avatares humanos + 1 mascote) via Agnes Studio.
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-lg text-xs">🔍 Dário</span>
          <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded-lg text-xs">📋 Conselheiro</span>
          <span className="px-2 py-1 bg-pink-500/10 text-pink-400 rounded-lg text-xs">✍️ Tonho</span>
          <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded-lg text-xs">🎨 Zé do Traço</span>
          <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded-lg text-xs">✅ Dona Benta</span>
        </div>
      </div>
      <button
        onClick={() => router.push("/admin/fabrica-ofertas")}
        className="px-4 py-2 bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] hover:from-[#7c3aed] hover:to-[#db2777] text-white rounded-xl text-sm font-medium transition-all"
      >
        Acessar Fábrica
      </button>
    </div>
  </div>
)}
```

---

## Exemplo de Posicionamento no Render

**ANTES:**
```tsx
{tab === "fabrica-blog" && (
  <div>✎ Fábrica de Blogs...</div>
)}

{tab === "fabrica-ebook" && (
  <div>❐ Fábrica de Ebooks...</div>
)}

{tab === "fabrica-curso" && (
  <div>▣ Fábrica de Cursos...</div>
)}
```

**DEPOIS:**
```tsx
{tab === "fabrica-ofertas" && (
  <div className="bg-[#111827] rounded-2xl border border-[#1e293b] p-6">
    <div className="flex items-start justify-between">
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          🎯 Fábrica de Ofertas
        </h3>
        <p className="text-gray-400 text-sm mt-1">
          Dário + Team — Investigação, Modelagem, Copy e Personagens
        </p>
        <p className="text-gray-500 text-xs mt-2 max-w-xl">
          Crie ofertas escaláveis com investigação automática de Facebook Ads 
          (20 anúncios escalados) + Google SEO (keywords + backlinks), 
          modelagem estratégica, copywriting de alta conversão e geração 
          de personagens (2 avatares humanos + 1 mascote) via Agnes Studio.
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-lg text-xs">🔍 Dário</span>
          <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded-lg text-xs">📋 Conselheiro</span>
          <span className="px-2 py-1 bg-pink-500/10 text-pink-400 rounded-lg text-xs">✍️ Tonho</span>
          <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded-lg text-xs">🎨 Zé do Traço</span>
          <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded-lg text-xs">✅ Dona Benta</span>
        </div>
      </div>
      <button
        onClick={() => router.push("/admin/fabrica-ofertas")}
        className="px-4 py-2 bg-gradient-to-r from-[#8b5cf6] to-[#ec4899] hover:from-[#7c3aed] hover:to-[#db2777] text-white rounded-xl text-sm font-medium transition-all"
      >
        Acessar Fábrica
      </button>
    </div>
  </div>
)}

{tab === "fabrica-blog" && (
  <div>✎ Fábrica de Blogs...</div>
)}

{tab === "fabrica-ebook" && (
  <div>❐ Fábrica de Ebooks...</div>
)}

{tab === "fabrica-curso" && (
  <div>▣ Fábrica de Cursos...</div>
)}
```

---

## Arquivo para Editar

```
C:\Users\jonat\Desktop\dezafira3.0\club-frontend\app\admin\page.tsx
```

---

## Resultado Final

Após adicionar e recarregar (Ctrl+R), o menu ficará:

```
Fábricas
├─ 🎯 Ofertas ← PRIMEIRO
├─ ❐ Ebook
├─ ▣ Curso
├─ ✎ Blog
├─ 🖼️ Capas Agnes
├─ 🎬 VSL
├─ 🔗 Bio Sites
├─ 📱 MiniApps
├─ 🎯 Blueprint
└─ 📦 Produtos
```

---

*Adicione o código acima no INÍCIO da lista de tabs e no INÍCIO do render, e recarregue a página!*
