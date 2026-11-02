import Link from "next/link";

export const metadata = { title: "Terms — RegIntel" };

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 py-6 text-sm leading-6 text-slate-300">
      <Link href="/" className="text-xs text-slate-500 hover:text-slate-300">
        ← RegIntel
      </Link>
      <h1 className="text-2xl font-semibold text-slate-100">Terms</h1>
      <p>
        RegIntel is an informational tool. It is not legal advice and it does not
        create a lawyer client relationship.
      </p>
      <p>
        Verdicts and answers are produced by a language model from the documents
        you provide and the regulation we index. Every quote is checked against
        its source, but a correct quote can still support a wrong conclusion.
        Verify anything you act on.
      </p>
      <p>
        The service is provided as is, without warranty. Coverage of regulators,
        documents and amendment language is partial and stated in the product.
      </p>
    </div>
  );
}
