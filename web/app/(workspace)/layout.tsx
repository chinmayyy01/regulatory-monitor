import { WorkspaceShell } from "@/components/WorkspaceShell";

export default function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <WorkspaceShell authDisabled={process.env.AUTH_DISABLED === "true"}>
      {children}
    </WorkspaceShell>
  );
}
