import { FrictionProvider } from "../_components/FrictionMeter";
import { LeftNav, PatientBanner, TopBar } from "../_components/Shell";

export default function EhrLayout({ children }: { children: React.ReactNode }) {
  return (
    <FrictionProvider>
      <div className="flex h-screen flex-col bg-slate-200 text-slate-800">
        <TopBar />
        <PatientBanner />
        <div className="flex min-h-0 flex-1">
          <LeftNav />
          <main className="min-w-0 flex-1 overflow-y-auto bg-slate-100 p-4">
            {children}
          </main>
        </div>
        <footer className="flex-shrink-0 border-t border-slate-300 bg-slate-200 px-3 py-1 text-[10px] text-slate-500">
          eClinicalWorks V12 (demo mockup) · Logged in as D. Alvarez · Berkeley
          Internal Medicine Associates · Session secured
        </footer>
      </div>
    </FrictionProvider>
  );
}
