import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


def _configure_client():
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)


def _build_prompt(team1: dict, team2: dict) -> str:
    return f"""
Responda SOMENTE em português do Brasil.

Analise os dados abaixo e responda de forma simples, objetiva e sem markdown.

{team1['info']['name']}:
- Pontos: {team1['stats']['points']}
- Pontos sofridos: {team1['stats']['points_allowed']}
- Rebotes: {team1['stats']['rebounds']}
- Assistências: {team1['stats']['assists']}
- Turnovers: {team1['stats']['turnovers']}

{team2['info']['name']}:
- Pontos: {team2['stats']['points']}
- Pontos sofridos: {team2['stats']['points_allowed']}
- Rebotes: {team2['stats']['rebounds']}
- Assistências: {team2['stats']['assists']}
- Turnovers: {team2['stats']['turnovers']}

REGRAS:
- Menos pontos sofridos = melhor defesa
- Mais rebotes = vantagem física
- Menos turnovers = melhor controle
- NÃO invente nada
- NÃO use negrito, listas, títulos ou markdown

RESPONDA EM UM ÚNICO PARÁGRAFO CURTO COM 3 OU 4 FRASES:
- Quem está melhor no geral
- Principais vantagens de cada time
- Quem deve vencer
"""


def _extract_finish_reason_name(response) -> str:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return ""

    finish_reason = getattr(candidates[0], "finish_reason", None)
    if hasattr(finish_reason, "name"):
        return finish_reason.name
    return str(finish_reason or "")


def _clean_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _looks_truncated(text: str, finish_reason_name: str) -> bool:
    cleaned = _clean_text(text)
    if not cleaned:
        return True
    if finish_reason_name == "MAX_TOKENS":
        return True
    if len(cleaned) < 80:
        return True
    return cleaned[-1] not in ".!?"


def _generate_analysis_with_gemini(prompt: str, max_output_tokens: int) -> tuple[str, str]:
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_output_tokens,
            temperature=0.4,
        ),
    )
    text = _clean_text(getattr(response, "text", "") or "")
    finish_reason_name = _extract_finish_reason_name(response)
    return text, finish_reason_name


def _build_fallback_analysis(team1: dict, team2: dict) -> str:
    team1_name = team1["info"]["name"]
    team2_name = team2["info"]["name"]
    team1_stats = team1["stats"]
    team2_stats = team2["stats"]

    team1_score = 0
    team2_score = 0

    if team1_stats["points"] > team2_stats["points"]:
        team1_score += 1
    elif team2_stats["points"] > team1_stats["points"]:
        team2_score += 1

    if team1_stats["points_allowed"] < team2_stats["points_allowed"]:
        team1_score += 1
    elif team2_stats["points_allowed"] < team1_stats["points_allowed"]:
        team2_score += 1

    if team1_stats["rebounds"] > team2_stats["rebounds"]:
        team1_score += 1
    elif team2_stats["rebounds"] > team1_stats["rebounds"]:
        team2_score += 1

    if team1_stats["assists"] > team2_stats["assists"]:
        team1_score += 1
    elif team2_stats["assists"] > team1_stats["assists"]:
        team2_score += 1

    if team1_stats["turnovers"] < team2_stats["turnovers"]:
        team1_score += 1
    elif team2_stats["turnovers"] < team1_stats["turnovers"]:
        team2_score += 1

    general_better = team1_name if team1_score >= team2_score else team2_name
    likely_winner = general_better

    team1_edges = []
    team2_edges = []

    if team1_stats["points"] > team2_stats["points"]:
        team1_edges.append("maior produção ofensiva")
    if team1_stats["points_allowed"] < team2_stats["points_allowed"]:
        team1_edges.append("defesa mais eficiente")
    if team1_stats["rebounds"] > team2_stats["rebounds"]:
        team1_edges.append("mais força nos rebotes")
    if team1_stats["turnovers"] < team2_stats["turnovers"]:
        team1_edges.append("melhor controle da posse")

    if team2_stats["points"] > team1_stats["points"]:
        team2_edges.append("maior produção ofensiva")
    if team2_stats["points_allowed"] < team1_stats["points_allowed"]:
        team2_edges.append("defesa mais eficiente")
    if team2_stats["rebounds"] > team1_stats["rebounds"]:
        team2_edges.append("mais força nos rebotes")
    if team2_stats["turnovers"] < team1_stats["turnovers"]:
        team2_edges.append("melhor controle da posse")

    team1_summary = ", ".join(team1_edges[:2]) or "equilíbrio estatístico"
    team2_summary = ", ".join(team2_edges[:2]) or "equilíbrio estatístico"

    return (
        f"No geral, o {general_better} chega um pouco melhor neste confronto. "
        f"O {team1_name} tem como principais trunfos {team1_summary}, enquanto o {team2_name} se apoia em {team2_summary}. "
        f"Pelos números atuais, o {likely_winner} aparece como a escolha mais segura para vencer."
    )


def generate_analysis(team1: dict, team2: dict) -> str:
    _configure_client()
    prompt = _build_prompt(team1, team2)

    try:
        text, finish_reason_name = _generate_analysis_with_gemini(prompt, 512)
        if not _looks_truncated(text, finish_reason_name):
            return text

        logger.warning(
            "Gemini analysis appears truncated (finish_reason=%s, text=%r); retrying with larger output window",
            finish_reason_name,
            text,
        )

        retry_text, retry_finish_reason_name = _generate_analysis_with_gemini(prompt, 1024)
        if not _looks_truncated(retry_text, retry_finish_reason_name):
            return retry_text

        logger.warning(
            "Gemini analysis remained truncated (finish_reason=%s, text=%r); using deterministic fallback",
            retry_finish_reason_name,
            retry_text,
        )
        return _build_fallback_analysis(team1, team2)
    except Exception as e:
        logger.error("Gemini analysis failed: %s", e)
        return _build_fallback_analysis(team1, team2)
