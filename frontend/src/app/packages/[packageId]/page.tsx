import { api } from "@/lib/api";
import { PackageDetailView } from "@/components/packages/PackageDetailView";
import { AnomalyExplanation } from "@/components/packages/AnomalyExplanation";
import Link from "next/link";
import { ArrowLeft, ServerCrash } from "lucide-react";

// Note: In Next.js 15+, params is a Promise
type Params = Promise<{ packageId: string }>;

export default async function PackageDetailPage(props: { params: Params }) {
  const params = await props.params;
  const { packageId } = params;

  let data = null;
  let errorObj: unknown = null;

  try {
    const res = await api.getPackage(packageId);
    data = res.data;
  } catch (error: unknown) {
    errorObj = error;
  }

  if (errorObj || !data) {
    const err = errorObj as Record<string, unknown>;
    const isNotFound = err?.status === 404;

    return (
      <div className="flex-1 bg-surface-50 dark:bg-surface-950 py-24">
        <div className="container mx-auto px-4 max-w-xl text-center">
          <div className="w-20 h-20 mx-auto bg-surface-200 dark:bg-surface-800 rounded-full flex items-center justify-center mb-6">
            <ServerCrash className="h-10 w-10 text-surface-500" />
          </div>
          <h1 className="text-3xl font-bold text-surface-900 dark:text-white mb-4">
            {isNotFound ? "Paket Tidak Ditemukan" : "Terjadi Kesalahan"}
          </h1>
          <p className="text-surface-600 dark:text-surface-400 mb-8 leading-relaxed">
            {isNotFound
              ? `Data paket dengan ID ${packageId} tidak terdapat dalam dataset (manifest) kami saat ini.`
              : (err?.message as string) || "Gagal menghubungi server backend."}
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-primary-600 hover:bg-primary-500 rounded-lg transition-colors shadow-sm"
          >
            Kembali ke Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-50 dark:bg-surface-950 py-12">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="mb-6">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-sm font-medium text-surface-500 hover:text-primary-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Kembali ke Dashboard
          </Link>
        </div>

        <PackageDetailView data={data} />

        <div className="mt-12 mb-6">
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white tracking-tight">
            Analisis Prioritas Pemeriksaan
          </h2>
        </div>

        <AnomalyExplanation data={data} />
      </div>
    </div>
  );
}
