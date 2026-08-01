"""
Quiz Master — Agente especialista em gerar perguntas de quiz.
Gera questoes de multiple choice para cada aula do curso.
"""
import json
from agents.llm import query_llm


class CourseQuizMaster:
    """Gera perguntas de quiz para aulas de curso."""

    async def generate_quiz(self, topic: str, module_title: str,
                            lesson_title: str, lesson_content: str,
                            num_questions: int = 5,
                            language: str = "pt") -> list:
        """
        Gera perguntas de quiz baseadas no conteudo da aula.
        Retorna lista de: {pergunta, alternativas: [a,b,c,d], resposta_correta}
        """
        # Truncar conteudo para nao estourar contexto
        content_preview = lesson_content[:2000]

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um especialista em avaliacoes educacionais. "
                f"Gere {num_questions} perguntas de multiple choice baseadas no conteudo da aula. "
                "Cada pergunta deve ter 4 alternativas (A, B, C, D) com apenas 1 correta. "
                "As perguntas devem testar compreensao, nao apenas memorizacao. "
                "Nivel: intermediario.\n\n"
                "Retorne APENAS um JSON valido (sem markdown, sem ```). "
                "Formato: "
                '{"questoes": [{"pergunta": "...", "alternativas": {"a": "...", "b": "...", "c": "...", "d": "..."}, "resposta_correta": "a", "explicacao": "..."}]}'
            )},
            {"role": "user", "content": (
                f"Topico do curso: {topic}\n"
                f"Modulo: {module_title}\n"
                f"Aula: {lesson_title}\n"
                f"Conteudo da aula:\n{content_preview}\n\n"
                f"Gere as {num_questions} perguntas de quiz."
            )},
        ])
        try:
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(resp)
            return data.get("questoes", [])
        except Exception:
            return []

    async def generate_module_quiz(self, topic: str, module_title: str,
                                    lessons: list, num_questions: int = 10,
                                    language: str = "pt") -> list:
        """
        Gera quiz consolidado de um modulo inteiro.
        lessons: [{title, content}]
        """
        content_summary = "\n".join([
            f"- {l['title']}: {l.get('content', '')[:500]}"
            for l in lessons[:10]
        ])

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um especialista em avaliacoes educacionais. "
                f"Gere {num_questions} perguntas de multiple choice que revisem TODO o conteudo do modulo. "
                "Distribua as perguntas entre as aulas do modulo. "
                "Cada pergunta deve ter 4 alternativas com apenas 1 correta. "
                "Retorne APENAS um JSON valido (sem markdown, sem ```). "
                "Formato: "
                '{"questoes": [{"pergunta": "...", "alternativas": {"a": "...", "b": "...", "c": "...", "d": "..."}, "resposta_correta": "a", "aula": "titulo da aula"}]}'
            )},
            {"role": "user", "content": (
                f"Topico: {topic}\n"
                f"Modulo: {module_title}\n"
                f"Aulas:\n{content_summary}\n\n"
                f"Gere o quiz consolidado do modulo."
            )},
        ])
        try:
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(resp)
            return data.get("questoes", [])
        except Exception:
            return []


# Singleton
course_quizmaster = CourseQuizMaster()
