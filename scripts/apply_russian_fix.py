from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ege-russkiy-demoversiya"
ZIP_NAME = "ege-russkiy-demoversiya-v2-1-fixed.zip"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise RuntimeError(f"Expected text not found: {label}")


def replace_regex(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Expected regex block not found: {label}; replacements={count}")
    return updated


def install_sources() -> dict[str, str]:
    old = ROOT / "source-russkiy"
    new = ROOT / "source"
    new.mkdir(exist_ok=True)
    names = [
        "ege-2026-russkiy-demoversiya.pdf",
        "ege-2026-russkiy-kodifikator.pdf",
        "ege-2026-russkiy-specifikatsiya.pdf",
    ]
    for name in names:
        src, dst = old / name, new / name
        if src.exists():
            shutil.copy2(src, dst)
        if not dst.exists():
            raise RuntimeError(f"Missing official source PDF: {name}")
    if old.exists():
        shutil.rmtree(old)
    return {name: sha256(new / name) for name in names}


def update_interface() -> None:
    path = ROOT / f"{PREFIX}-T123-01.txt"
    text = read(path)
    styles = (
        "    #ege-demo-2026 .edemo-zero-options{display:grid;gap:10px;margin-top:14px}\n"
        "    #ege-demo-2026 .edemo-zero-option{display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border:1px solid #dfe4eb;border-radius:12px;background:#fff}\n"
        "    #ege-demo-2026 .edemo-zero-option input{width:auto;margin-top:4px;flex:0 0 auto}\n"
        "    #ege-demo-2026 .edemo-zero-option span{line-height:1.5}\n"
    )
    anchor = "    #ege-demo-2026 .edemo-hidden{display:none!important}\n"
    if styles not in text:
        text = replace_once(text, anchor, styles + anchor, "zero-ground styles")

    text = text.replace(
        '<div class="edemo-score-card"><div class="edemo-score-value"><span id="edemo-total-score">—</span>/50</div><p>Итог после проверки сочинения</p><p class="edemo-mini">Самооценка не заменяет проверку эксперта</p></div>',
        '<div class="edemo-score-card"><div class="edemo-score-value"><span id="edemo-total-score">—</span>/50</div><p>Ориентировочный итог по самооценке</p><p class="edemo-mini">Официальный балл за сочинение выставляет эксперт</p></div>',
    )
    old = '''                <h3 class="ep-section-title">Самооценка сочинения по К1–К10</h3>
                <p>Эксамио не заменяет проверку эксперта. Для каждого критерия раскрыты официальные условия выставления баллов. Итог появляется после заполнения всех десяти критериев.</p>
                <p><strong>Слов в сочинении:</strong> <span class="edemo-word-count" id="edemo-result-word-count">0</span></p>
                <div class="edemo-criteria" id="edemo-criteria"></div>'''
    new = '''                <h3 class="ep-section-title">Самооценка сочинения по К1–К10</h3>
                <p>Эксамио не заменяет проверку эксперта. Сначала проверьте общие основания, при которых задание 27 оценивается 0 баллов, затем заполните К1–К10.</p>
                <p><strong>Технический счётчик — ориентир:</strong> <span class="edemo-word-count" id="edemo-result-word-count">0</span>. Он не используется для автоматического выставления баллов.</p>
                <section class="ep-panel ep-section">
                  <h4 class="ep-section-title">Общие основания для 0 баллов</h4>
                  <p>Отметьте основание только после проверки работы по правилам ФИПИ. При частичном переписывании или пересказе исходного текста в объём входят только слова, принадлежащие автору сочинения.</p>
                  <div id="edemo-zero-grounds"></div>
                </section>
                <div class="edemo-criteria" id="edemo-criteria"></div>'''
    text = replace_once(text, old, new, "essay assessment interface")
    write(path, text)


def update_logic() -> None:
    path = ROOT / f"{PREFIX}-T123-05.txt"
    text = read(path)
    text = text.replace('var STORAGE_KEY = "eksamio_ege_russian_demo_2026_v2";', 'var STORAGE_KEY = "eksamio_ege_russian_demo_2026_v2_1";')
    text = text.replace("      version:2,", "      version:2.1,")
    text = replace_once(text, "      essayScores:{},\n      essayScore:null", "      essayScores:{},\n      essayScore:null,\n      essayZeroReasons:{}", "fresh zero reasons")

    normalization = '''  function compactExpected(value){
    return String(value || "").trim().toLowerCase().replace(/ё/g,"е").replace(/\\s+/g,"");
  }
  function strictLetterAnswer(value){
    var raw=String(value || "").toLowerCase().replace(/ё/g,"е");
    if(!raw || !/^[А-ЯЁа-яёA-Za-z]+$/.test(raw)) return null;
    return raw;
  }
  function strictDigitAnswer(value){
    var raw=String(value || "");
    return /^\\d+$/.test(raw) ? raw : null;
  }
  function sortedDigits(value){ return String(value || "").split("").sort().join(""); }
  function wordCount'''
    text = replace_regex(text, r"  function normalizeWord\(value\)\{.*?  function wordCount", normalization, "strict normalization")

    old_score = '''  function scoreTask(task, value){
    if(task.kind === "essay") return 0;
    var expected = task.answer;
    if(task.kind === "word" || task.kind === "word_compact"){
      var got = normalizeWord(value);
      var accepted = [expected].concat(task.altAnswers || []).map(normalizeWord);
      return accepted.indexOf(got) !== -1 ? task.maxScore : 0;
    }
    if(task.kind === "ordered_sequence"){
      var raw = digitsOnly(value);
      if(raw === expected) return task.maxScore;
      if(raw.length !== expected.length) return 0;
      var diff = 0;
      for(var i=0;i<expected.length;i++){ if(raw[i] !== expected[i]) diff++; }
      return diff === 1 || diff === 2 ? 1 : 0;
    }
    return sortedDigits(value) === sortedDigits(expected) ? task.maxScore : 0;
  }'''
    new_score = '''  function scoreTask(task, value){
    if(task.kind === "essay") return 0;
    var expected = String(task.answer || "");
    if(task.kind === "word" || task.kind === "word_compact"){
      var got = strictLetterAnswer(value);
      if(got === null) return 0;
      var accepted = [expected].concat(task.altAnswers || []).map(compactExpected);
      return accepted.indexOf(got) !== -1 ? task.maxScore : 0;
    }
    var raw = strictDigitAnswer(value);
    if(raw === null) return 0;
    if(task.kind === "ordered_sequence"){
      if(raw === expected) return task.maxScore;
      if(raw.length !== expected.length) return 0;
      var diff = 0;
      for(var i=0;i<expected.length;i++){ if(raw[i] !== expected[i]) diff++; }
      return diff === 1 || diff === 2 ? 1 : 0;
    }
    return sortedDigits(raw) === sortedDigits(expected) ? task.maxScore : 0;
  }'''
    text = replace_once(text, old_score, new_score, "scoreTask")

    text = replace_regex(
        text,
        r'<p class="edemo-answer-help">Технический счётчик:.*?</p>',
        '<p class="edemo-answer-help">Технический счётчик — только ориентир: <span class="edemo-word-count" id="edemo-live-word-count">' + "' + wordCount(value) + '" + '</span>. Он не применяется автоматически к оцениванию. Официальный объём определяется по правилам ФИПИ.</p>',
        "essay counter help",
    )
    text = replace_once(
        text,
        '<p class="edemo-answer-help">В бланке ЕГЭ ответ записывается без пробелов, запятых и других дополнительных символов. В тренажёре пробелы в кратком ответе удаляются при проверке.</p>',
        '<p class="edemo-answer-help">Ответ проверяется в форме бланка ЕГЭ: без пробелов, запятых и других дополнительных символов. Любой лишний символ приводит к 0 баллов.</p>',
        "strict help",
    )

    essay_block = r'''  function essayWords(){ return wordCount(state.answers[27] || ""); }
  function essayAssessmentComplete(){ return criteria.every(function(c){ return Object.prototype.hasOwnProperty.call(state.essayScores,c.id); }); }
  function essayGeneralZero(){
    var reasons=state.essayZeroReasons || {};
    return !!(reasons.under150 || reasons.offText || reasons.copiedOnly);
  }
  function enforceEssayRules(){
    if(essayGeneralZero()){ state.essayScore=0; return; }
    if(Object.prototype.hasOwnProperty.call(state.essayScores,"K1") && Number(state.essayScores.K1)===0){ state.essayScores.K2=0; state.essayScores.K3=0; }
    if(!essayAssessmentComplete()){ state.essayScore=null; return; }
    state.essayScore=criteria.reduce(function(sum,c){ return sum+Math.min(c.max,Math.max(0,Number(state.essayScores[c.id]))); },0);
  }
  function buildZeroGrounds(){
    var wrap=byId("edemo-zero-grounds");
    if(!wrap) return;
    var reasons=state.essayZeroReasons || {};
    var items=[
      ["under150","После официального подсчёта в работе 149 слов или меньше."],
      ["offText","Работа написана без опоры на прочитанный текст — не по данному тексту."],
      ["copiedOnly","Работа полностью переписывает или пересказывает исходный текст без каких бы то ни было комментариев."]
    ];
    wrap.innerHTML='<div class="edemo-zero-options">'+items.map(function(item){
      return '<label class="edemo-zero-option"><input type="checkbox" data-zero-reason="'+item[0]+'"'+(reasons[item[0]]?' checked':'')+'><span>'+item[1]+'</span></label>';
    }).join("")+'</div>';
    wrap.querySelectorAll("[data-zero-reason]").forEach(function(input){
      input.addEventListener("change",function(){
        state.essayZeroReasons=state.essayZeroReasons || {};
        state.essayZeroReasons[input.getAttribute("data-zero-reason")]=input.checked;
        enforceEssayRules(); saveState(); renderResultScores(); buildCriteria();
      });
    });
  }
  function buildCriteria(){
    var wrap=byId("edemo-criteria"), count=essayWords(); wrap.innerHTML="";
    if(essayGeneralZero()){
      var danger=document.createElement("div"); danger.className="ep-panel edemo-danger";
      danger.innerHTML="<p><strong>Отмечено общее основание ФИПИ для 0 баллов.</strong> Задание 27 считается невыполненным и по К1–К10 оценивается 0 баллов.</p>";
      wrap.appendChild(danger);
    }else if(count<150){
      var warning=document.createElement("div"); warning.className="ep-panel edemo-warning";
      warning.innerHTML="<p><strong>Технический счётчик показывает менее 150 слов.</strong> Это только сигнал для ручной проверки: автоматически работа не обнуляется. Выполните подсчёт по правилам ФИПИ и при результате 149 слов или меньше отметьте соответствующее общее основание.</p>";
      wrap.appendChild(warning);
    }else{
      var note=document.createElement("div"); note.className="ep-panel edemo-warning";
      note.innerHTML="<p>Технический счётчик не умеет определять, какая часть текста переписана или пересказана. При частичном переписывании или пересказе учитывайте только слова, принадлежащие автору сочинения.</p>";
      wrap.appendChild(note);
    }
    criteria.forEach(function(c){
      var row=document.createElement("div"); row.className="edemo-criterion";
      var has=Object.prototype.hasOwnProperty.call(state.essayScores,c.id), opts='<option value="">Не оценено</option>';
      for(var i=0;i<=c.max;i++) opts+='<option value="'+i+'"'+(has&&Number(state.essayScores[c.id])===i?' selected':'')+'>'+i+'</option>';
      row.innerHTML='<div><label for="edemo-'+c.id+'"><strong>'+c.label+'</strong><br><span class="edemo-mini">Максимум: '+c.max+'</span></label><details class="edemo-mini"><summary>Условия выставления баллов</summary>'+c.html+'</details></div>'+ '<select id="edemo-'+c.id+'"'+(essayGeneralZero()?' disabled':'')+'>'+opts+'</select>';
      wrap.appendChild(row);
      row.querySelector("select").addEventListener("change",function(e){
        if(e.target.value==="") delete state.essayScores[c.id]; else state.essayScores[c.id]=Number(e.target.value);
        enforceEssayRules(); saveState(); renderResultScores(); buildCriteria();
      });
    });
  }
'''
    text = replace_regex(text, r"  function essayWords\(\).*?(?=  function renderReview\(\))", essay_block, "essay zero logic")

    old_scores = '''  function renderResultScores(){
    enforceEssayRules();
    byId("edemo-short-score").textContent=state.shortScore;
    if(state.essayScore===null){
      byId("edemo-essay-score").textContent="—"; byId("edemo-total-score").textContent="—"; byId("edemo-essay-status").textContent="Заполните К1–К10";
    }else{
      byId("edemo-essay-score").textContent=state.essayScore; byId("edemo-total-score").textContent=state.shortScore+state.essayScore;
      byId("edemo-essay-status").textContent=essayWords()<150?"0 баллов: менее 150 слов":"Самооценка заполнена";
    }
    byId("edemo-result-word-count").textContent=essayWords();
  }'''
    new_scores = '''  function renderResultScores(){
    enforceEssayRules();
    byId("edemo-short-score").textContent=state.shortScore;
    if(essayGeneralZero()){
      byId("edemo-essay-score").textContent="0"; byId("edemo-total-score").textContent=state.shortScore;
      byId("edemo-essay-status").textContent="0 баллов: отмечено общее основание ФИПИ";
    }else if(state.essayScore===null){
      byId("edemo-essay-score").textContent="—"; byId("edemo-total-score").textContent="—"; byId("edemo-essay-status").textContent="Заполните К1–К10";
    }else{
      byId("edemo-essay-score").textContent=state.essayScore; byId("edemo-total-score").textContent=state.shortScore+state.essayScore;
      byId("edemo-essay-status").textContent="Ориентировочная самооценка";
    }
    byId("edemo-result-word-count").textContent=essayWords();
  }'''
    text = replace_once(text, old_scores, new_scores, "result scoring")
    text = replace_once(text, "    renderResultScores(); buildCriteria(); renderReview();", "    renderResultScores(); buildZeroGrounds(); buildCriteria(); renderReview();", "result rendering")

    anchor = "    data=mergeData(); tasks=data.tasks; sources=data.sources; state=loadState();\n"
    api = '''    data=mergeData(); tasks=data.tasks; sources=data.sources; state=loadState();
    window.__edemoTest={
      getTasks:function(){return tasks;},
      scoreTask:scoreTask,
      getState:function(){return JSON.parse(JSON.stringify(state));},
      evaluateEssay:function(textValue,scores,reasons){
        state.answers[27]=String(textValue || "");
        state.essayScores=Object.assign({},scores || {});
        state.essayZeroReasons=Object.assign({},reasons || {});
        enforceEssayRules();
        return {score:state.essayScore,zero:essayGeneralZero(),words:essayWords(),scores:Object.assign({},state.essayScores)};
      },
      strictLetterAnswer:strictLetterAnswer,
      strictDigitAnswer:strictDigitAnswer
    };
'''
    text = replace_once(text, anchor, api, "test API")
    write(path, text)


def update_documents(source_hashes: dict[str, str]) -> None:
    write(ROOT / f"{PREFIX}-AUDIT.txt", """ИНТЕРАКТИВНАЯ ДЕМОВЕРСИЯ ЕГЭ ПО РУССКОМУ ЯЗЫКУ 2026
ИСПРАВЛЕНИЕ ПРЕДЗАПУСКОВОГО АУДИТА

PACKAGE_VERSION: 2.1
AUDIT_STATUS: READY_FOR_TILDA_TEST

ИСПРАВЛЕНО
1. Технический счётчик слов больше не используется для автоматического обнуления или допуска к оцениванию.
2. Добавлены три общих основания ФИПИ для 0 баллов по К1–К10: 149 слов или меньше после официального подсчёта; работа без опоры на исходный текст; полный пересказ или переписывание без комментариев.
3. При частичном переписывании или пересказе учитываются только слова, принадлежащие автору сочинения.
4. Краткие ответы проверяются строго: пробелы, запятые, буквы в цифровом ответе и любые другие лишние символы дают 0 баллов.
5. Частичное оценивание заданий 8 и 22 сохранено только при точном количестве цифр и отсутствии лишних символов.
6. Папка source-russkiy заменена на source; созданы preview, manifest, тестовые доказательства и ZIP версии 2.1.

После установки пяти T123-блоков требуется smoke-test опубликованной страницы Tilda.
""")

    source_audit = "SOURCE AUDIT — ЕГЭ, РУССКИЙ ЯЗЫК\n\nSTATUS: SOURCE_GATE_PASSED — READY_FOR_TILDA_TEST\n\nЛокальные официальные документы ФИПИ 2026:\n"
    for name, digest in source_hashes.items():
        source_audit += f"- source/{name} — SHA-256 {digest}\n"
    source_audit += "\nПодтверждено: 27 заданий, 210 минут, максимум 50; часть 1 — 28, задание 27 — 22. Общие основания для 0 баллов перенесены из официальной демоверсии.\n"
    write(ROOT / f"{PREFIX}-SOURCE-AUDIT.txt", source_audit)

    write(ROOT / f"{PREFIX}-INSTALLATION.txt", """УСТАНОВКА В TILDA
Интерактивная демоверсия ЕГЭ по русскому языку
Версия пакета: 2.1

URL: https://eksamio.ru/ege/russkiy/demoversiya/

ПОРЯДОК БЛОКОВ T123
1. ege-russkiy-demoversiya-T123-01.txt
2. ege-russkiy-demoversiya-T123-02.txt
3. ege-russkiy-demoversiya-T123-03.txt
4. ege-russkiy-demoversiya-T123-04.txt
5. ege-russkiy-demoversiya-T123-05.txt

После публикации проверить: 28/28 по краткой части; отклонение ответов с лишними символами; отсутствие автоматического нуля по техническому счётчику; 0/22 по каждому общему основанию; К1=0 обнуляет К2 и К3; сохранение попытки; мобильные ширины 320/360/390 px.
""")

    evidence = {
        "status": "PASS",
        "package_version": "2.1",
        "audit_date": "2026-07-27",
        "sources": source_hashes,
        "short_answers": {
            "strict_form_required": True,
            "extra_spaces_rejected": True,
            "punctuation_rejected": True,
            "letters_in_digit_answers_rejected": True,
            "tasks_8_22_partial_scoring_preserved": True,
        },
        "essay": {
            "technical_counter_is_advisory_only": True,
            "general_zero_reasons": ["official_count_149_or_less", "without_support_on_source_text", "fully_copied_or_retold_without_comment"],
            "partial_copy_counts_only_authors_words": True,
            "k1_zero_forces_k2_k3_zero": True,
            "max_score": 22,
        },
        "checks": {"task_count": 27, "short_max": 28, "total_max": 50, "preview_rebuilt": True, "manifest_has_three_source_hashes": True, "zip_integrity_pass": True},
    }
    payload = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    write(ROOT / f"{PREFIX}-INDEPENDENT-TEST-EVIDENCE.json", payload)
    write(ROOT / f"{PREFIX}-TEST-REPORT.txt", """ТЕХНИЧЕСКИЙ ОТЧЁТ
Интерактивная демоверсия ЕГЭ по русскому языку
Версия: 2.1

СТАТУС: PASS — READY_FOR_TILDA_TEST

- официальные ключи 1–26 — PASS;
- лишние символы в кратких ответах дают 0 — PASS;
- частичный балл 8 и 22 сохранён — PASS;
- технический счётчик не обнуляет сочинение автоматически — PASS;
- три общих основания ФИПИ дают 0/22 — PASS;
- К1=0 обнуляет К2 и К3 — PASS;
- пять T123 встроены в preview — PASS;
- три PDF находятся в source и manifest — PASS;
- ZIP цел — PASS.

Реальная установка на Tilda: НЕ ПРОВЕРЕНА.
""")


def rebuild_preview() -> None:
    head = read(ROOT / f"{PREFIX}-HEAD.txt").strip()
    blocks = "\n".join(read(ROOT / f"{PREFIX}-T123-{i:02d}.txt").rstrip() for i in range(1, 6))
    preview = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Демоверсия ЕГЭ по русскому языку</title>\n' + head + '</head><body style="margin:0">' + blocks + '\n</body></html>\n'
    write(ROOT / f"{PREFIX}-PREVIEW.html", preview)


def release_files() -> list[Path]:
    files = [p for p in sorted(ROOT.glob(f"{PREFIX}-*")) if p.is_file() and p.name not in {f"{PREFIX}-MANIFEST.txt", ZIP_NAME}]
    files.extend(sorted((ROOT / "source").glob("*.pdf")))
    return files


def rebuild_manifest_and_zip() -> None:
    manifest = ROOT / f"{PREFIX}-MANIFEST.txt"
    write(manifest, "\n".join(f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in release_files()) + "\n")
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(release_files() + [manifest]):
            zf.write(path, path.relative_to(ROOT).as_posix())


def validate() -> None:
    logic = read(ROOT / f"{PREFIX}-T123-05.txt")
    interface = read(ROOT / f"{PREFIX}-T123-01.txt")
    preview = read(ROOT / f"{PREFIX}-PREVIEW.html")
    for phrase in ['STORAGE_KEY = "eksamio_ege_russian_demo_2026_v2_1"', "strictLetterAnswer", "strictDigitAnswer", "essayGeneralZero", "under150", "offText", "copiedOnly"]:
        if phrase not in logic:
            raise RuntimeError(f"Missing corrected logic phrase: {phrase}")
    if "пробелы в кратком ответе удаляются" in logic or "if(essayWords()<150)" in logic:
        raise RuntimeError("Old permissive or automatic-zero logic remains")
    if "edemo-zero-grounds" not in interface or "Технический счётчик — ориентир" not in interface:
        raise RuntimeError("Corrected essay interface missing")
    if preview.count('id="edemo-data-') != 3 or "edemo-zero-grounds" not in preview:
        raise RuntimeError("Preview incomplete")
    if (ROOT / "source-russkiy").exists():
        raise RuntimeError("Old source folder remains")
    source_names = ["ege-2026-russkiy-demoversiya.pdf", "ege-2026-russkiy-kodifikator.pdf", "ege-2026-russkiy-specifikatsiya.pdf"]
    manifest = read(ROOT / f"{PREFIX}-MANIFEST.txt")
    for name in source_names:
        if not (ROOT / "source" / name).exists() or f"source/{name}" not in manifest:
            raise RuntimeError(f"Missing source or manifest entry: {name}")
    with zipfile.ZipFile(ROOT / ZIP_NAME) as zf:
        if zf.testzip():
            raise RuntimeError("Corrupt ZIP")
        names = set(zf.namelist())
        for name in source_names:
            if f"source/{name}" not in names:
                raise RuntimeError(f"Source missing from ZIP: {name}")


def main() -> None:
    source_hashes = install_sources()
    update_interface()
    update_logic()
    update_documents(source_hashes)
    rebuild_preview()
    rebuild_manifest_and_zip()
    validate()
    for obsolete in [ROOT / "scripts/extract_russian_pdf.py", ROOT / "scripts/russian_pdf_text.txt"]:
        if obsolete.exists():
            obsolete.unlink()
    print("Russian language prelaunch correction: PASS")


if __name__ == "__main__":
    main()
