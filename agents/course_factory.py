"""
Course Factory — Agentes especialistas em producao de cursos em texto.
Gera cursos completos com modulos, aulas, materiais, exercicios e quizzes.
"""
import os
from typing import List, Dict, Any

from agents.llm import query_llm


class CourseWriterAgent:
    """Agente escritor de cursos - gera conteudo didatico em texto."""

    async def generate_course_structure(self, topic: str, num_modules: int = 4) -> list:
        """Gera a estrutura do curso (modulos e aulas)."""
        nl = chr(10)
        prompt = (
            f"Crie um curso cristao sobre: {topic}.{nl}"
            f"Gere {num_modules} modulos. Para cada modulo, forneca: {nl}"
            f"- Titulo do modulo{nl}"
            f"- 2-3 aulas dentro do modulo{nl}"
            f"- Descricao breve do modulo{nl}{nl}"
            f"Formato: MODULO N|Titulo|Descricao|Aula 1|Aula 2|Aula 3"
        )
        resp = await query_llm([
            {"role": "system", "content": "Voce e um educador cristao e teologo."},
            {"role": "user", "content": prompt},
        ])
        modules = []
        for line in resp.strip().split(nl):
            if "|" in line and line.startswith("MODULO"):
                parts = line.split("|")
                if len(parts) >= 3:
                    try:
                        num = int(parts[0].replace("MODULO", "").strip())
                        title = parts[1].strip()
                        desc = parts[2].strip()
                        lessons = [p.strip() for p in parts[3:] if p.strip()]
                        modules.append({"module_number": num, "title": title, "description": desc, "lessons": lessons})
                    except ValueError:
                        continue
        if not modules:
            for i in range(num_modules):
                modules.append({"module_number": i+1, "title": f"Modulo {i+1}", "description": "", "lessons": [f"Aula {i+1}.1"]})
        return modules

    async def write_lesson(self, topic: str, module_title: str, lesson_title: str, lesson_number: int) -> str:
        """Escreve o conteudo de uma aula."""
        nl = chr(10)
        prompt = (
            f"Escreva a aula \"{lesson_title}\" do modulo \"{module_title}\" do curso sobre: {topic}.{nl}{nl}"
            f"A aula deve conter:{nl}"
            f"- Introducao ao tema (2 paragrafos){nl}"
            f"- Desenvolvimento com base biblica (3-4 paragrafos){nl}"
            f"- Aplicacao pratica (2 paragrafos){nl}"
            f"- Conclusao e reflexao (1 paragrafo){nl}"
            f"- Pergunta para reflexao{nl}{nl}"
            f"Tom: Didatico, profundo, acessivel. Portugues brasileiro."
        )
        return await query_llm([
            {"role": "system", "content": "Voce e um professor de teologia. Escreva em portugues brasileiro."},
            {"role": "user", "content": prompt},
        ], max_tokens=4096)

    async def generate_course(self, topic: str, course_title: str, num_modules: int = 4) -> dict:
        """Gera o curso completo."""
        structure = await self.generate_course_structure(topic, num_modules)
        modules_result = []
        for mod in structure:
            lessons = []
            for i, lesson_title in enumerate(mod["lessons"]):
                content = await self.write_lesson(topic, mod["title"], lesson_title, i+1)
                lessons.append({"title": lesson_title, "content": content, "lesson_number": i+1})
            modules_result.append({
                "module_number": mod["module_number"],
                "title": mod["title"],
                "description": mod["description"],
                "lessons": lessons,
            })
        return {"title": course_title, "topic": topic, "modules": modules_result}
