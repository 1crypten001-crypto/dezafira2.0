"""
Pedagogo — Agente especialista em conteudo didatico.
Escreve o conteudo completo de cada aula de forma didatica e envolvente.
"""
from agents.llm import query_llm


class CoursePedagogue:
    """Escreve conteudo de aulas de curso de forma didatica."""

    async def write_lesson(self, topic: str, module_title: str,
                           lesson_title: str, lesson_number: int,
                           lesson_type: str = "texto",
                           module_number: int = 1,
                           total_modules: int = 4,
                           total_lessons_in_module: int = 4,
                           language: str = "pt") -> dict:
        """Escreve o conteudo completo de uma aula."""
        progresso = f"Modulo {module_number}/{total_modules}, Aula {lesson_number}/{total_lessons_in_module}"

        if lesson_type == "exercicio":
            return await self._write_exercise(topic, module_title, lesson_title, language)

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um professor pedagogo especialista em educacao online. "
                "Escreva o conteudo de uma aula de curso online de forma:\n"
                "- Didatica e clara\n"
                "- Com exemplos praticos\n"
                "- Com emojis moderados para engajamento\n"
                "- Em paragrafos curtos (max 3-4 frases)\n"
                "- Com topicos e subtopicos bem definidos\n"
                "- Minimo 500 palavras, maximo 1500 palavras\n"
                "- Em portugues brasileiro\n\n"
                "Estrutura da aula:\n"
                "1. Titulo da aula como H2\n"
                "2. Introducao envolvente (por que essa aula importa?)\n"
                "3. Conteudo principal com exemplos\n"
                "4. Resumo rapido (bullet points)\n"
                "5. Exercicio pratico ou reflexao\n"
                "6. Proxima aula: preview\n\n"
                "Retorne APENAS o conteudo HTML (sem ```html)."
            )},
            {"role": "user", "content": (
                f"Curso sobre: {topic}\n"
                f"Modulo: {module_title}\n"
                f"Aula: {lesson_title}\n"
                f"Progresso: {progresso}\n\n"
                f"Escreva o conteudo completo desta aula."
            )},
        ])
        content = resp.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        word_count = len(content.split())
        estimated_minutes = max(5, word_count // 200)

        return {
            "content": content,
            "word_count": word_count,
            "estimated_minutes": estimated_minutes,
        }

    async def _write_exercise(self, topic: str, module_title: str,
                               lesson_title: str, language: str = "pt") -> dict:
        """Escreve um exercicio pratico."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um professor pedagogo. Crie um exercicio pratico para uma aula de curso online. "
                "O exercicio deve ter:\n"
                "1. Instrucao clara do que fazer\n"
                "2. Contexto do exercicio\n"
                "3. Passo a passo (3-5 passos)\n"
                "4. Dicas de sucesso\n"
                "Retorne APENAS o conteudo HTML (sem ```html)."
            )},
            {"role": "user", "content": (
                f"Topico: {topic}\n"
                f"Modulo: {module_title}\n"
                f"Aula: {lesson_title}\n"
                f"Crie o exercicio pratico."
            )},
        ])
        content = resp.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        word_count = len(content.split())
        return {
            "content": content,
            "word_count": word_count,
            "estimated_minutes": 15,
        }

    async def write_module_summary(self, topic: str, module_title: str,
                                    lessons_titles: list, language: str = "pt") -> str:
        """Gera um resumo do modulo ao final das aulas."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um professor pedagogo. Gere um resumo conciso do modulo "
                "em formato de lista com os pontos-chave aprendidos. "
                "Retorne APENAS o conteudo HTML."
            )},
            {"role": "user", "content": (
                f"Topico: {topic}\n"
                f"Modulo: {module_title}\n"
                f"Aulas: {', '.join(lessons_titles)}\n"
                f"Gere o resumo do modulo."
            )},
        ])
        return resp.strip()


# Singleton
course_pedagogue = CoursePedagogue()
