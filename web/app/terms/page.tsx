export const metadata = { title: "Terms — RegIntel" };

export default function TermsPage() {
  return (
    <div className="landing min-h-screen">
      <div className="mx-auto max-w-2xl space-y-6 px-6 py-16">
        <a href="/" className="app-link caption-2">
          ← RegIntel
        </a>
        <h1 className="heading-5 text-white">Terms</h1>
        <p className="body-6 text-[#D4D4D4]">
          RegIntel is an informational tool. It is not legal advice and it does not
          create a lawyer client relationship.
        </p>
        <p className="body-6 text-[#D4D4D4]">
          Verdicts and answers are produced by a language model from the documents you
          provide and the regulation we index. Every quote is checked against its
          source, but a correct quote can still support a wrong conclusion. Verify
          anything you act on.
        </p>
        <p className="body-6 text-[#D4D4D4]">
          The service is provided as is, without warranty. Coverage of regulators,
          documents and amendment language is partial and stated in the product.
        </p>
      </div>
    </div>
  );
}
