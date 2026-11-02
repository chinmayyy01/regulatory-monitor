import { Nav } from "@/components/landing/Nav";
import { Reveal } from "@/components/landing/Reveal";
import { TaglineReveal } from "@/components/landing/TaglineReveal";
import { Topography } from "@/components/landing/Topography";

const BENEFITS = [
  {
    title: "See the gap, not a summary",
    body: "Each obligation is checked against the clauses you already have, with a verdict and a quote from both sides.",
  },
  {
    title: "Know which version applies",
    body: "Clauses carry validity windows, so a question can be answered as of a date instead of against whatever text happened to rank highest.",
  },
  {
    title: "Ask in plain language",
    body: "Answers come back as claims with the exact sentence attached. A claim we cannot verify is dropped, not softened.",
  },
  {
    title: "Catch the change",
    body: "A diff between two mapping runs shows which of your policies stopped covering an obligation, and which newly do.",
  },
];

const STEPS = [
  {
    title: "Add your policies",
    body: "Upload the PDFs you already maintain. They are parsed into clauses, not blended into one blob.",
  },
  {
    title: "We map the obligations",
    body: "Every applicable obligation is matched against your clauses and judged, with quotes kept as evidence.",
  },
  {
    title: "Review and fix",
    body: "Filter to what is missing or partial, edit the policy, then re check. The next run shows what moved.",
  },
];

const FAQ = [
  {
    q: "Which regulators do you cover?",
    a: "RBI and SEBI today. The ingestion and mapping pipeline is not specific to either, so another regulator is a data problem rather than a rewrite.",
  },
  {
    q: "What happens to my documents?",
    a: "PDFs are parsed and embedded on the server. When a verdict or an answer is generated, the relevant excerpts are sent to the configured model provider. Documents are not used to train anything.",
  },
  {
    q: "Is this legal advice?",
    a: "No. It is a reading aid with citations. Every verdict points at the clause it came from, and every answer quote is checked against the source before it is shown.",
  },
  {
    q: "How accurate is it?",
    a: "On our current evaluation set the system identifies the correct document 80 percent of the time and lands on the exact clause 38 percent of the time. It refused all eight questions the corpus could not answer. We publish the numbers we would rather not.",
  },
  {
    q: "What file types can I upload?",
    a: "Text based PDF files up to 10 MB. Scanned documents are rejected, because we will not cite text we cannot read.",
  },
  {
    q: "How are amendments handled?",
    a: "Each clause carries a validity window and amendments are recorded as relations between documents. Language that changes a clause indirectly is only partly captured today, and we say so rather than guess.",
  },
  {
    q: "Can I run it myself?",
    a: "Yes. Postgres with pgvector, a Python service and a Next frontend. Tenant isolation is enforced in the database, not only in application code.",
  },
  {
    q: "What does it cost?",
    a: "Pricing is not public yet. There is no charge while the evaluation set is still being expanded.",
  },
];

const STATS = [
  { value: "1,050", label: "documents indexed" },
  { value: "85,236", label: "clauses segmented" },
  { value: "16,883", label: "obligations extracted" },
];

export default function LandingPage() {
  return (
    <>
      <Nav />

      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      >
        <Topography />
      </div>

      <main id="main" className="relative z-10 mx-auto max-w-[1120px] px-6 pb-24">
        <section className="pt-24 pb-12">
          <h1 className="heading-1 balance max-w-[680px] bg-gradient-to-r from-white to-[#9B9B9B] bg-clip-text text-transparent">
            Every regulatory change, traced to the clause in your own policy.
          </h1>
          <p className="body-2 pretty mt-6 max-w-[680px] text-[#9B9B9B]">
            RegIntel reads RBI and SEBI circulars, extracts the obligations, and
            checks them against the policies you already have. Every verdict
            quotes both sides, so you can see exactly what to edit.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <a
              href="/login"
              className="button-md rounded-full bg-white px-3 py-2 text-black transition-transform duration-300 hover:scale-[1.02] active:scale-[0.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Request access
            </a>
            <span className="caption-2 text-[#9B9B9B]">
              No card. The demo tenant is seeded with four policies.
            </span>
          </div>
        </section>

        <Reveal>
          <section className="rounded-2xl border border-[#272727] bg-[#181818] p-2">
            <div className="rounded-lg bg-[#1F1F1F] p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="caption-3 uppercase tracking-wide text-[#9B9B9B]">
                    Obligation
                  </p>
                  <p className="title-2 mt-2 max-w-[680px] text-white">
                    Maintain disaggregated data of priority sector loans by
                    category and sub category.
                  </p>
                </div>
                <span className="caption-3 rounded-full bg-white px-3 py-1 text-black">
                  Satisfied
                </span>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="caption-4 text-[#9B9B9B]">Regulation</p>
                  <p className="body-6 pretty mt-2 text-[#D4D4D4]">
                    The Company shall maintain disaggregated data of priority
                    sector loans by category and sub category.
                  </p>
                </div>
                <div>
                  <p className="caption-4 text-[#9B9B9B]">Your policy</p>
                  <p className="body-6 pretty mt-2 text-[#D4D4D4]">
                    The Company shall maintain disaggregated data of priority
                    sector loans by category and sub category.
                  </p>
                </div>
              </div>

              <p className="caption-2 mt-6 text-[#9B9B9B]">
                Priority Sector Lending Policy, section 6.1
              </p>
            </div>
          </section>
        </Reveal>

        <Reveal>
          <section className="mt-12 grid gap-6 pt-10 sm:grid-cols-3">
            {STATS.map((stat) => (
              <div key={stat.label}>
                <p className="heading-4 text-white">{stat.value}</p>
                <p className="caption-1 mt-2 text-[#9B9B9B]">{stat.label}</p>
              </div>
            ))}
          </section>
        </Reveal>

        <section id="benefits" className="mt-24 scroll-mt-24">
          <Reveal>
            <h2 className="heading-3 balance max-w-[680px] text-white">
              A reading aid that shows its work.
            </h2>
          </Reveal>
          <div className="mt-10 grid gap-10 sm:grid-cols-2">
            {BENEFITS.map((benefit) => (
              <Reveal key={benefit.title}>
                <h3 className="title-1 text-white">{benefit.title}</h3>
                <p className="body-3 pretty mt-3 text-[#9B9B9B]">
                  {benefit.body}
                </p>
              </Reveal>
            ))}
          </div>
        </section>

        <section id="how" className="mt-24 scroll-mt-24">
          <Reveal>
            <h2 className="heading-3 balance max-w-[680px] text-white">
              Three steps, then a diff.
            </h2>
          </Reveal>
          <div className="mt-10 grid gap-10 sm:grid-cols-3">
            {STEPS.map((step, index) => (
              <Reveal key={step.title}>
                <p className="caption-3 text-[#9B9B9B]">
                  {String(index + 1).padStart(2, "0")}
                </p>
                <h3 className="title-1 mt-3 text-white">{step.title}</h3>
                <p className="body-3 pretty mt-3 text-[#9B9B9B]">{step.body}</p>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="mt-24 py-24">
          <TaglineReveal text="Rules move. Your policies should move with them." />
        </section>

        <section id="faq" className="mt-24 scroll-mt-24">
          <Reveal>
            <h2 className="heading-3 balance max-w-[680px] text-white">
              Questions we get before a trial.
            </h2>
          </Reveal>
          <div className="mt-10 grid gap-3">
            {FAQ.map((item) => (
              <Reveal key={item.q}>
                <details className="group rounded-2xl border border-[#272727] bg-[#181818]">
                  <summary className="title-3 flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-4 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                    {item.q}
                    <span
                      aria-hidden
                      className="text-[#9B9B9B] transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] group-open:rotate-45"
                    >
                      +
                    </span>
                  </summary>
                  <p className="body-3 pretty px-6 pb-6 text-[#9B9B9B]">
                    {item.a}
                  </p>
                </details>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="mt-24 rounded-2xl border border-[#272727] bg-[#181818] p-6">
          <Reveal>
            <div className="flex flex-wrap items-center justify-between gap-6">
              <div>
                <h2 className="heading-4 balance max-w-[680px] text-white">
                  See it against your own policies.
                </h2>
                <p className="body-3 mt-3 max-w-[680px] text-[#9B9B9B]">
                  The demo tenant ships with four policies and a set of
                  verdicts, so there is something to read on the first screen.
                </p>
              </div>
              <a
                href="/login"
                className="button-md rounded-full bg-white px-3 py-2 text-black transition-transform duration-300 hover:scale-[1.02] active:scale-[0.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                Request access
              </a>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="relative z-10 border-t border-[#272727]">
        <div className="mx-auto flex max-w-[1120px] flex-wrap items-center justify-between gap-4 px-6 py-10">
          <p className="caption-2 text-[#9B9B9B]">
            RegIntel. Informational, not legal advice.
          </p>
          <div className="flex items-center gap-6">
            <a href="/privacy" className="caption-2 text-[#9B9B9B] hover:text-white">
              Privacy
            </a>
            <a href="/terms" className="caption-2 text-[#9B9B9B] hover:text-white">
              Terms
            </a>
            <span className="caption-2 text-[#9B9B9B]">© 2026</span>
          </div>
        </div>
      </footer>
    </>
  );
}
