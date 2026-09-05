import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  answerCurrentQuestion,
  candidateFrontier,
  eligibleQuestions,
  evaluate,
  nextStep,
  noAnswerLabels,
  researchCatalog,
  type ResponseState,
} from "../../packages/flavor-data/src/research";
import {
  createSession,
  exportSession,
  type Paraphrase,
  type PostTask,
  type Session,
  type Stratum,
} from "../../packages/flavor-data/src/research/session";
import "../styles/research.css";

export function meta() {
  return [
    { title: "Coffee Flavor · 用户任务研究" },
    { name: "robots", content: "noindex, nofollow" },
  ];
}

type Screen =
  | "setup"
  | "value"
  | "paraphrase"
  | "c0"
  | "c1"
  | "question"
  | "results"
  | "post"
  | "done";
const elapsed = (start: number) =>
  Math.max(0, Math.round(performance.now() - start));

export default function ResearchHarness() {
  const [screen, setScreen] = useState<Screen>("setup");
  const [session, setSession] = useState<Session | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [download, setDownload] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [valueRead, setValueRead] = useState(false);
  const clock = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const questionId = session ? nextStep(session.state).question?.id : null;
  useEffect(() => {
    clock.current = performance.now();
    heading.current?.focus();
  }, [screen, questionId]);
  useEffect(() => {
    if (screen !== "value") return;
    const timeout = window.setTimeout(() => setValueRead(true), 5000);
    return () => window.clearTimeout(timeout);
  }, [screen]);
  useEffect(
    () => () => {
      if (download) URL.revokeObjectURL(download);
    },
    [download],
  );

  function setup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const next = createSession(
        String(form.get("researchId")),
        crypto.randomUUID(),
        form.get("stratum") as Stratum,
        performance.now(),
      );
      setSession(next);
      setScreen("value");
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "请检查研究编号");
    }
  }

  function respond(responseState: ResponseState) {
    if (!session) return;
    const step = nextStep(session.state);
    if (!step.question) return;
    const before = candidateFrontier(session.state);
    const answerSelections = responseState === "SELECTED" ? selected : [];
    const state = answerCurrentQuestion(
      session.state,
      answerSelections,
      responseState,
      session.q5Accepted,
    );
    const after = candidateFrontier(state);
    const following = nextStep(state);
    const next: Session = {
      ...session,
      state,
      questions: [
        ...session.questions,
        {
          questionId: step.question.id,
          semanticKey: step.question.semanticKey,
          optionIdsShown: step.question.options.map((o) => o.id),
          selectedOptionIds: answerSelections,
          responseState,
          responseTimeMs: elapsed(clock.current),
          candidateIdsBefore: before,
          candidateIdsAfter: after,
          candidateCountBefore: before.length,
          candidateCountAfter: after.length,
          selectedOptionCount: answerSelections.length,
          allOptionsSelected:
            answerSelections.length === step.question.options.length,
          remainingEligibleAxes: eligibleQuestions(state).map(
            (q) => q.question.id,
          ),
          selectionReason: step.reason,
        },
      ],
      earlyStopReason:
        following.question && !following.recovery ? "" : following.reason,
      q5Offered: session.q5Offered || following.recovery,
      q5TriggerReason: following.recovery
        ? following.reason
        : session.q5TriggerReason,
    };
    setSession(next);
    setSelected([]);
    setScreen(
      following.question && !following.recovery ? "question" : "results",
    );
  }

  function finish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) return;
    const f = new FormData(event.currentTarget);
    const post: PostTask = {
      firstQuestionComprehension: f.get(
        "comprehension",
      ) as PostTask["firstQuestionComprehension"],
      partialOutputAcceptance: f.get(
        "partial",
      ) as PostTask["partialOutputAcceptance"],
      reuseIntent: f.get("reuse") as PostTask["reuseIntent"],
      completedWithoutHelp: f.get("help") === "yes",
      difficulty: f.get("difficulty") as PostTask["difficulty"],
    };
    try {
      const data = exportSession(
        session,
        Number(f.get("helpfulness")),
        post,
        performance.now(),
      );
      setDownload(
        URL.createObjectURL(
          new Blob([JSON.stringify(data, null, 2) + "\n"], {
            type: "application/json",
          }),
        ),
      );
      setScreen("done");
      setError("");
    } catch {
      setError("记录未通过校验，请检查回答后再导出。");
    }
  }

  const result = session ? evaluate(session.state) : null;
  const step = session ? nextStep(session.state) : null;
  const title = {
    setup: "准备开始",
    value: "把这杯咖啡的感觉说出来",
    paraphrase: "你觉得它能帮你做什么？",
    c0: "这杯咖啡是怎么做的？",
    c1: "包装上写的烘焙程度是？",
    question: step?.question?.prompt ?? "风味联想",
    results: "目前的风味联想",
    post: "最后六个简短问题",
    done: "谢谢，研究任务已完成",
  }[screen];

  return (
    <section className="research-shell" lang="zh-Hans">
      <p className="research-kicker">Coffee Flavor · 用户任务研究</p>
      <h1 ref={heading} tabIndex={-1}>
        {title}
      </h1>
      {error && <p role="alert">{error}</p>}
      {screen === "setup" && (
        <form onSubmit={setup}>
          <p>
            本次约 5–8
            分钟。回答只保留在当前页面，完成后可下载给研究者。刷新页面会清除本次过程。
          </p>
          <label>
            研究编号
            <input
              name="researchId"
              pattern="R3O-[0-9]{3}"
              placeholder="R3O-001"
              autoComplete="off"
              required
            />
          </label>
          <p className="research-note">请使用研究者提供的编号。</p>
          <label>
            你与咖啡的接触
            <select name="stratum" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="novice">很少接触 / 刚开始了解</option>
              <option value="regular">平时经常喝</option>
              <option value="experienced">有较多品鉴或专业经验</option>
            </select>
          </label>
          <button type="submit">开始任务</button>
        </form>
      )}
      {screen === "value" && (
        <>
          <p className="research-lead">
            回答几个关于这杯咖啡的问题，找一些词来描述你闻到、喝到的感觉。
          </p>
          <p>这些词是供你尝试的参照。你可以觉得不贴切，也可以暂时说不清。</p>
          <button disabled={!valueRead} onClick={() => setScreen("paraphrase")}>
            读完了
          </button>
        </>
      )}
      {screen === "paraphrase" && session && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            setSession({
              ...session,
              valuePropositionParaphraseResult: f.get(
                "paraphrase",
              ) as Paraphrase,
            });
            setScreen("c0");
          }}
        >
          <p>请用自己的话告诉研究者。研究者只记录理解情况。</p>
          <label>
            研究者记录
            <select name="paraphrase" defaultValue="" required>
              <option value="" disabled>
                请选择
              </option>
              <option value="correct">理解：用词语帮助描述自己的感受</option>
              <option value="partial">部分理解</option>
              <option value="incorrect">理解成其他用途</option>
              <option value="not_assessed">未记录</option>
            </select>
          </label>
          <button type="submit">继续</button>
        </form>
      )}
      {screen === "c0" && session && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            setSession({
              ...session,
              state: { ...session.state, c0: String(f.get("c0")) },
              c0SelectionTimeMs: elapsed(clock.current),
            });
            setScreen("c1");
          }}
        >
          <fieldset>
            <legend>选择最接近这一杯的做法</legend>
            {researchCatalog.preparations.map((p) => (
              <label className="research-option" key={p.id}>
                <input type="radio" name="c0" value={p.id} required />
                <span>
                  {p.label}
                  <small>{p.examples}</small>
                </span>
              </label>
            ))}
          </fieldset>
          <button type="submit">继续</button>
        </form>
      )}
      {screen === "c1" && session && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            const roast = String(f.get("c1"));
            setSession({
              ...session,
              state: {
                ...session.state,
                c1: roast === "UNSURE" ? null : roast,
              },
              c1SelectionTimeMs: elapsed(clock.current),
            });
            setScreen("question");
          }}
        >
          <p>
            优先参考包装名称：Light 通常接近浅，Medium 接近中，Dark
            接近深。品牌的叫法可能不同，不知道时可以选“不确定”。
          </p>
          <fieldset>
            <legend>从浅到深的七档</legend>
            {researchCatalog.roasts.map((r) => (
              <label className="research-option" key={r.id}>
                <input type="radio" name="c1" value={r.id} required />
                <span>{r.label}</span>
              </label>
            ))}
          </fieldset>
          <label className="research-option">
            <input type="radio" name="c1" value="UNSURE" required />
            <span>不确定 / 包装没有写</span>
          </label>
          <button type="submit">开始风味问题</button>
        </form>
      )}
      {screen === "question" && session && step?.question && (
        <>
          <p>第 {session.questions.length + 1} 道风味问题</p>
          <p>选择所有明显符合的项目，通常 1–2 项就够了。</p>
          <fieldset>
            <legend className="research-sr-only">可以多选</legend>
            {step.question.options.map((o) => (
              <label className="research-option" key={o.id}>
                <input
                  type="checkbox"
                  checked={selected.includes(o.id)}
                  onChange={() =>
                    setSelected((s) =>
                      s.includes(o.id)
                        ? s.filter((id) => id !== o.id)
                        : [...s, o.id],
                    )
                  }
                />
                <span>
                  {o.label}
                  {o.examples && <small>{o.examples}</small>}
                </span>
              </label>
            ))}
          </fieldset>
          <button
            disabled={!selected.length}
            onClick={() => respond("SELECTED")}
          >
            确认选择
          </button>
          <div className="research-escapes">
            {(
              Object.keys(noAnswerLabels) as Array<keyof typeof noAnswerLabels>
            ).map((state) => (
              <button
                className="research-secondary"
                key={state}
                onClick={() => respond(state)}
              >
                {noAnswerLabels[state]}
              </button>
            ))}
          </div>
          <p className="research-note">
            不确定：分不清。都不像：眼前这些例子都不贴切。跳过：暂时不回答。
          </p>
          {session.questions.length > 0 && (
            <button
              className="research-secondary"
              onClick={() => {
                setSession({
                  ...session,
                  earlyStopReason: "PARTICIPANT_REQUESTED_PARTIAL_RESULT",
                });
                setSelected([]);
                setScreen("results");
              }}
            >
              先看当前结果
            </button>
          )}
        </>
      )}
      {screen === "results" && session && result && (
        <>
          <p>这是根据你目前回答提供的参照，不是这杯咖啡唯一正确的描述。</p>
          <h2>目前最明确</h2>
          {result.headline.length ? (
            <ul className="research-results">
              {result.headline.map((c) => (
                <li key={c.id}>
                  <h3>{c.label}</h3>
                  <p>{c.explanation}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p>证据还不够明确，暂时没有主要风味联想。</p>
          )}
          {result.resultState === "ABSTAINED_CONFLICT" && (
            <p>前后的联想还不一致，可以先保留自己的感觉。</p>
          )}
          {(result.expandedMain.length > 0 ||
            result.exploration.length > 0) && (
            <>
              <button
                className="research-secondary"
                aria-expanded={expanded}
                aria-controls="expanded-results"
                onClick={() => {
                  setExpanded(!expanded);
                  setSession({ ...session, expandClicked: true });
                }}
              >
                {expanded ? "收起更多联想" : "展开更多联想"}
              </button>
              {expanded && (
                <div id="expanded-results">
                  {result.expandedMain.length > 0 && (
                    <>
                      <h2>其他有支持的联想</h2>
                      <ul>
                        {result.expandedMain.map((c) => (
                          <li key={c.id}>
                            <strong>{c.label}</strong>
                            <p>{c.explanation}</p>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                  {result.exploration.length > 0 && (
                    <>
                      <h2>还可以继续留意</h2>
                      <ul>
                        {result.exploration.map((c) => (
                          <li key={c.id}>
                            <strong>{c.label}</strong>
                            <p>{c.explanation}</p>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}
            </>
          )}
          {step?.recovery && step.question && (
            <div className="research-recovery">
              <p>再想一个有区分的问题，可能帮助你把感觉说得更具体。</p>
              <button
                onClick={() => {
                  setSession({
                    ...session,
                    q5Accepted: true,
                    extraQuestionClicked: true,
                  });
                  setSelected([]);
                  setScreen("question");
                }}
              >
                再回答一题，让结果更具体
              </button>
              <button
                className="research-secondary"
                onClick={() => setScreen("post")}
              >
                先看当前结果
              </button>
            </div>
          )}
          <label className="research-option">
            <input
              type="checkbox"
              checked={session.state.openSet}
              onChange={(e) =>
                setSession({
                  ...session,
                  state: { ...session.state, openSet: e.target.checked },
                  earlyStopReason: e.target.checked
                    ? "PARTICIPANT_REPORTED_OPEN_SET"
                    : (() => {
                        const restored = nextStep({
                          ...session.state,
                          openSet: false,
                        });
                        return restored.question && !restored.recovery
                          ? "PARTICIPANT_REQUESTED_PARTIAL_RESULT"
                          : restored.reason;
                      })(),
                })
              }
            />
            <span>我想描述的感觉在这些方向之外</span>
          </label>
          <button onClick={() => setScreen("post")}>完成后续反馈</button>
        </>
      )}
      {screen === "post" && (
        <form onSubmit={finish}>
          <label>
            1. 当前结果对你描述这杯咖啡有多大帮助？
            <select name="helpfulness" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                  {n === 1 ? " · 没有帮助" : n === 5 ? " · 很有帮助" : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            2. 第一道风味题的意思清楚吗？
            <select name="comprehension" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="clear">清楚</option>
              <option value="partial">部分清楚</option>
              <option value="unclear">不清楚</option>
            </select>
          </label>
          <label>
            3. 结果少于三个时，你能接受吗？
            <select name="partial" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="accept">能接受</option>
              <option value="unsure">不确定</option>
              <option value="reject">不能接受</option>
              <option value="not_applicable">本次没有遇到</option>
            </select>
          </label>
          <label>
            4. 下次喝不熟悉的咖啡，你还会使用吗？
            <select name="reuse" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="yes">会</option>
              <option value="maybe">可能</option>
              <option value="no">不会</option>
            </select>
          </label>
          <label>
            5. 除了记录复述，你是否独立完成了任务？
            <select name="help" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="yes">是</option>
              <option value="no">需要研究者帮助</option>
            </select>
          </label>
          <label>
            6. 哪一部分最费力？
            <select name="difficulty" required defaultValue="">
              <option value="" disabled>
                请选择
              </option>
              <option value="none">都还好</option>
              <option value="context">选择咖啡背景</option>
              <option value="wording">理解词语</option>
              <option value="choices">在选项间做选择</option>
              <option value="results">理解结果</option>
            </select>
          </label>
          <button type="submit">生成本地研究记录</button>
        </form>
      )}
      {screen === "done" && download && session && (
        <>
          <p>记录包含研究编号、选择与用时。你可以下载后交给研究者。</p>
          <a
            className="research-download"
            href={download}
            download={`coffee-study-${session.participantResearchId}.json`}
          >
            下载本次记录 JSON
          </a>
        </>
      )}
    </section>
  );
}
