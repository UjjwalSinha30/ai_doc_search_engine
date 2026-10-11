import { Activity, FileText, MessageSquareText, ShieldCheck } from "lucide-react";

export default function AuthLayout({ title, subtitle, children }) {
  const features = [
    { icon: FileText, label: "Upload and search documents" },
    { icon: MessageSquareText, label: "Ask cited follow-up questions" },
    { icon: ShieldCheck, label: "Private per-user workspace" },
    { icon: Activity, label: "LangSmith trace visibility" },
  ];

  return (
    <div className="min-h-screen grid bg-gray-50 text-gray-950 dark:bg-gray-950 dark:text-gray-100 lg:grid-cols-[1fr_520px]">
      <section className="hidden border-r border-gray-200 bg-white px-10 py-10 dark:border-gray-800 dark:bg-gray-950 lg:flex lg:flex-col lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-sm font-semibold text-white">
              MV
            </div>
            <div>
              <p className="text-sm font-semibold">MindVault</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Private document intelligence
              </p>
            </div>
          </div>

          <div className="mt-20 max-w-xl">
            <h1 className="text-4xl font-semibold tracking-tight">
              Ask better questions across your documents.
            </h1>
            <p className="mt-4 text-sm leading-6 text-gray-600 dark:text-gray-400">
              Upload files, retrieve grounded context, and inspect cited answers with a local-first RAG workflow.
            </p>
          </div>
        </div>

        <div className="grid gap-3">
          {features.map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
                <Icon className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              </div>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </section>

      <main className="flex items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-sm font-semibold text-white">
                MV
              </div>
              <div>
                <p className="text-sm font-semibold">MindVault</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Private document intelligence
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <div className="mb-8">
              <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
            </div>

            {children}
          </div>

          <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-500">
            Your documents stay isolated to your account.
          </p>
        </div>
      </main>
    </div>
  );
}