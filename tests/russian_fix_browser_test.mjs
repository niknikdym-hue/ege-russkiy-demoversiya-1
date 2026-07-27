import fs from 'node:fs';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

const html = fs.readFileSync('ege-russkiy-demoversiya-PREVIEW.html', 'utf8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'https://eksamio.ru/ege/russkiy/demoversiya/',
  beforeParse(window) {
    window.scrollTo = () => {};
    window.confirm = () => true;
  },
});

if (dom.window.document.readyState === 'loading') {
  await new Promise((resolve) => dom.window.document.addEventListener('DOMContentLoaded', resolve, { once: true }));
}
await new Promise((resolve) => setTimeout(resolve, 0));

const api = dom.window.__edemoTest;
assert.ok(api, 'test API is available');
const tasks = api.getTasks();
assert.equal(tasks.length, 27, '27 task positions');

let checkedVariants = 0;
let checkedAlternativeAnswers = 0;
for (const base of tasks.filter((task) => task.number <= 26)) {
  const variants = base.variants?.length ? base.variants : [{}];
  for (const variant of variants) {
    const task = { ...base, ...variant };
    const correct = task.kind === 'word' || task.kind === 'word_compact'
      ? String(task.answer).replace(/\s+/g, '')
      : String(task.answer);
    assert.equal(api.scoreTask(task, correct), task.maxScore, `official key ${task.number}`);
    for (const alternative of task.altAnswers || []) {
      const compactAlternative = String(alternative).replace(/\s+/g, '');
      assert.equal(api.scoreTask(task, compactAlternative), task.maxScore, `official alternative ${task.number}: ${alternative}`);
      assert.equal(api.scoreTask(task, `${compactAlternative} `), 0, `space rejected in alternative ${task.number}: ${alternative}`);
      checkedAlternativeAnswers += 1;
    }
    assert.equal(api.scoreTask(task, `${correct}!`), 0, `punctuation rejected ${task.number}`);
    assert.equal(api.scoreTask(task, `${correct} `), 0, `space rejected ${task.number}`);
    if (task.kind !== 'word' && task.kind !== 'word_compact') {
      assert.equal(api.scoreTask(task, `${correct}а`), 0, `letter rejected in digits ${task.number}`);
    }
    if (task.kind === 'unordered_digits' && correct.length > 1) {
      assert.equal(api.scoreTask(task, [...correct].reverse().join('')), task.maxScore, `permitted digit order ${task.number}`);
    }
    checkedVariants += 1;
  }
}
assert.equal(checkedVariants, 35, 'all 35 official short-answer examples checked');
assert.equal(checkedAlternativeAnswers, 4, 'all four official alternative answers checked');

for (const number of [8, 22]) {
  const base = tasks.find((task) => task.number === number);
  const expected = String(base.answer);
  const oneWrong = `${expected[0] === '9' ? '8' : '9'}${expected.slice(1)}`;
  const twoWrong = `${expected[0] === '9' ? '8' : '9'}${expected[1] === '8' ? '7' : '8'}${expected.slice(2)}`;
  const threeWrong = `${expected[0] === '9' ? '8' : '9'}${expected[1] === '8' ? '7' : '8'}${expected[2] === '7' ? '6' : '7'}${expected.slice(3)}`;
  assert.equal(api.scoreTask(base, oneWrong), 1, `one wrong position in ${number}`);
  assert.equal(api.scoreTask(base, twoWrong), 1, `two wrong positions in ${number}`);
  assert.equal(api.scoreTask(base, threeWrong), 0, `three wrong positions in ${number}`);
  assert.equal(api.scoreTask(base, `${expected}1`), 0, `extra digit in ${number}`);
  assert.equal(api.scoreTask(base, `${expected}!`), 0, `extra symbol in ${number}`);
}

const maxScores = { K1: 1, K2: 3, K3: 2, K4: 1, K5: 2, K6: 1, K7: 3, K8: 3, K9: 3, K10: 3 };
const shortText = Array.from({ length: 20 }, (_, i) => `слово${i}`).join(' ');
const advisory = api.evaluateEssay(shortText, maxScores, {});
assert.equal(advisory.words, 20, 'technical counter is visible');
assert.equal(advisory.score, 22, 'technical counter does not automatically zero the essay');
assert.equal(advisory.zero, false);

for (const reason of ['under150', 'offText', 'copiedOnly']) {
  const result = api.evaluateEssay(shortText, maxScores, { [reason]: true });
  assert.equal(result.score, 0, `${reason} gives zero`);
  assert.equal(result.zero, true, `${reason} is a general zero ground`);
}

const k1Zero = api.evaluateEssay(shortText, { ...maxScores, K1: 0 }, {});
assert.equal(k1Zero.scores.K2, 0, 'K1=0 forces K2=0');
assert.equal(k1Zero.scores.K3, 0, 'K1=0 forces K3=0');
assert.equal(k1Zero.score, 16, 'remaining criteria are summed correctly');

assert.ok(html.includes('Общие основания для 0 баллов'));
assert.ok(html.includes('Технический счётчик — ориентир'));
assert.ok(!html.includes('пробелы в кратком ответе удаляются'));

console.log(JSON.stringify({ status: 'PASS', checkedVariants, checkedAlternativeAnswers, essayGeneralZeroReasons: 3 }, null, 2));
