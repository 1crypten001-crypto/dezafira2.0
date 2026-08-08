"""
Professor — Agente especialista em estrutura curricular.
Define módulos, aulas, objetivos de aprendizado e pré-requisitos.
"""
import json
from agents.llm import query_llm


class CourseProfessor:
    """Gera a estrutura curricular completa de um curso."""

    async def analyze_audience(self, topic: str, language: str = "pt") -> dict:
        """Analisa público-alvo, nível e objetivos de aprendizado."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um professor universitario especialista em design instrucional. "
                "Analise o topic e retorne APENAS um JSON valido (sem markdown, sem ```). "
                "O JSON deve ter: "
                '{"publico_alvo": "descrição do público", '
                '"nivel": "iniciante|intermediario|avancado", '
                '"objetivos": ["objetivo 1", "objetivo 2", ...], '
                '"pre_requisitos": ["pré-requisito 1", ...], '
                '"carga_horaria_estimada": "X horas", '
                '"num_modulos_recomendado": 4, '
                '"num_aulas_por_modulo": 4}'
            )},
            {"role": "user", "content": f"Topic: {topic}\nIdioma: {language}"},
        ])
        try:
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(resp)
        except Exception:
            return {
                "publico_alvo": "Profissionais e estudantes interessados em " + topic,
                "nivel": "iniciante",
                "objetivos": [f"Compreender os fundamentos de {topic}"],
                "pre_requisitos": [],
                "carga_horaria_estimada": "8 horas",
                "num_modulos_recomendado": 4,
                "num_aulas_por_modulo": 4,
            }

    async def generate_structure(self, topic: str, course_title: str,
                                  num_modules: int = 4,
                                  num_lessons_per_module: int = 4,
                                  language: str = "pt") -> list:
        """Gera a estrutura de módulos e aulas (sem conteúdo)."""
        lessons_list = ", ".join([f"Aula {i+1}..." for i in range(num_lessons_per_module)])
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um professor universitario especialista em design instrucional. "
                f"Gere a estrutura curricular de um curso com {num_modules} modulos, "
                f"cada modulo com {num_lessons_per_module} aulas. "
                "Retorne APENAS um JSON valido (sem markdown, sem ```). "
                "Formato: "
                '{"modulos": [{"numero": 1, "titulo": "...", "descricao": "...", '
                '"aulas": [{"numero": 1, "titulo": "...", "tipo": "video|texto|exercicio"}]}]}'
            )},
            {"role": "user", "content": (
                f"Curso: {course_title}\n"
                f"Topico: {topic}\n"
                f"Modulos: {num_modules}\n"
                f"Aulas por modulo: {num_lessons_per_module}\n"
                f"Aulas do modulo 1 devem incluir: {lessons_list}\n"
                "Retorne o JSON estruturado."
            )},
        ])
        try:
            resp = resp.strip()
            if resp.startswith("```"):
                resp = resp.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(resp)
            return data.get("modulos", [])
        except Exception:
            # Fallback: estrutura generica
            modulos = []
            for i in range(num_modules):
                aulas = []
                for j in range(num_lessons_per_module):
                    aulas.append({
                        "numero": j + 1,
                        "titulo": f"Aula {j + 1}",
                        "tipo": "texto",
                    })
                modulos.append({
                    "numero": i + 1,
                    "titulo": f"Modulo {i + 1}",
                    "descricao": f"Conteudo do modulo {i + 1}",
                    "aulas": aulas,
                })
            return modulos

    async def generate_title(self, topic: str, language: str = "pt") -> str:
        """Gera um titulo magnetico para o curso."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter de infoprodutos. "
                "Crie um titulo magnetico e profissional (max 8 palavras) para um curso online. "
                "Retorne APENAS o titulo, sem aspas, sem pontuacao extra."
            )},
            {"role": "user", "content": f"Topico: {topic}\nIdioma: {language}"},
        ])
        return resp.strip().strip('"').strip("'")


# Singleton
course_professor = CourseProfessor()
