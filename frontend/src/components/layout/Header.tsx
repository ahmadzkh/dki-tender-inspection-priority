import Link from "next/link";
import { ActivitySquare, LayoutDashboard, FileSearch, Database, FlaskConical } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full glass border-b border-surface-200 dark:border-surface-800 transition-all duration-300">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 text-primary-600 dark:text-primary-400 font-semibold tracking-tight transition-opacity hover:opacity-80"
        >
          <ActivitySquare className="h-6 w-6" />
          <span className="hidden sm:inline-block">Prioritas Pemeriksaan Tender</span>
          <span className="sm:hidden">PPT DKI</span>
        </Link>

        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-surface-600 hover:text-primary-600 dark:text-surface-300 dark:hover:text-primary-400 transition-colors"
          >
            <LayoutDashboard className="h-4 w-4" />
            <span className="hidden sm:inline-block">Dashboard</span>
          </Link>
          <Link
            href="/dataset"
            className="flex items-center gap-2 text-surface-600 hover:text-primary-600 dark:text-surface-300 dark:hover:text-primary-400 transition-colors"
          >
            <Database className="h-4 w-4" />
            <span className="hidden sm:inline-block">Dataset</span>
          </Link>
          <Link
            href="/methodology"
            className="flex items-center gap-2 text-surface-600 hover:text-primary-600 dark:text-surface-300 dark:hover:text-primary-400 transition-colors"
          >
            <FileSearch className="h-4 w-4" />
            <span className="hidden sm:inline-block">Metodologi</span>
          </Link>
          <Link
            href="/evaluation"
            className="flex items-center gap-2 text-surface-600 hover:text-primary-600 dark:text-surface-300 dark:hover:text-primary-400 transition-colors"
          >
            <FlaskConical className="h-4 w-4" />
            <span className="hidden sm:inline-block">Evaluasi</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
