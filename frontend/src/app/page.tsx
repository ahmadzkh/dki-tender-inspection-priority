import { ArrowRight, BarChart3, ShieldAlert, Zap } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col flex-1">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 sm:py-32 lg:pb-32 xl:pb-36 bg-surface-950 text-white">
        {/* Background ambient glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary-600/20 rounded-full blur-3xl opacity-50 pointer-events-none" />

        <div className="container mx-auto px-4 relative z-10 text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-primary-200 text-sm font-medium mb-8 border border-white/10 backdrop-blur-sm">
            <span className="flex h-2 w-2 rounded-full bg-primary-400"></span>
            Skripsi Version 1.0 (Real Data)
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-8 leading-tight">
            Sistem Prioritas Pemeriksaan <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-linear-to-r from-primary-400 to-indigo-300">
              Realisasi Tender DKI Jakarta
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-surface-300 mb-10 max-w-2xl mx-auto leading-relaxed">
            Menemukan pola anomali pada data pengadaan menggunakan Isolation Forest.
            Dirancang khusus untuk mendukung Inspektorat dalam menentukan prioritas pemeriksaan paket tender.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-white bg-primary-600 hover:bg-primary-500 rounded-lg shadow-lg shadow-primary-900/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              Buka Dashboard Analitik
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="#methodology"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-white bg-surface-800 hover:bg-surface-700 rounded-lg border border-surface-700 transition-all"
            >
              Pelajari Metodologi
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-surface-50 dark:bg-surface-900/50">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Feature 1 */}
            <div className="glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300">
              <div className="h-12 w-12 bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400 rounded-xl flex items-center justify-center mb-6">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-surface-900 dark:text-white">Machine Learning</h3>
              <p className="text-surface-600 dark:text-surface-400 leading-relaxed">
                Menggunakan algoritma Isolation Forest untuk mendeteksi paket tender yang paling menyimpang dari tren pengadaan standar.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300">
              <div className="h-12 w-12 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-xl flex items-center justify-center mb-6">
                <Zap className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-surface-900 dark:text-white">Prioritas Cepat</h3>
              <p className="text-surface-600 dark:text-surface-400 leading-relaxed">
                Membantu auditor mengurangi waktu seleksi dari ribuan data LPSE menjadi daftar prioritas kerja yang rasional.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300 border-orange-200 dark:border-orange-900/30">
              <div className="h-12 w-12 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-xl flex items-center justify-center mb-6">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-surface-900 dark:text-white">Batas Klaim</h3>
              <p className="text-surface-600 dark:text-surface-400 leading-relaxed">
                Peringkat anomali adalah indikator kejanggalan statistik, bukan vonis korupsi, fraud, atau kolusi. Bukti hukum tetap bersandar pada temuan lapangan.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Methodology Section */}
      <section id="methodology" className="py-24 bg-white dark:bg-surface-950 scroll-mt-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-surface-900 dark:text-white sm:text-4xl">
              Metodologi Analisis
            </h2>
            <p className="mt-4 text-lg text-surface-600 dark:text-surface-400">
              Bagaimana sistem ini memproses data pengadaan publik
            </p>
          </div>

          <div className="space-y-12">
            <div className="flex gap-6">
              <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400 font-bold text-xl border border-primary-200 dark:border-primary-800">
                1
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-surface-900 dark:text-white">Data Integration</h3>
                <p className="text-surface-600 dark:text-surface-400">
                  Data realisasi tender ditarik dari INAPROC yang mencakup ratusan paket Pemprov DKI Jakarta (2024-2025). Data kemudian diperkaya dengan menarik riwayat jadwal terperinci dari portal LPSE terkait.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400 font-bold text-xl border border-primary-200 dark:border-primary-800">
                2
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-surface-900 dark:text-white">Feature Extraction</h3>
                <p className="text-surface-600 dark:text-surface-400">
                  Dari data mentah, sistem menghitung berbagai metrik krusial seperti persentase penurunan penawaran terhadap HPS, durasi evaluasi dokumen, dan rasio nilai kontrak terhadap pagu anggaran (financial & temporal anomalies).
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-400 font-bold text-xl border border-primary-200 dark:border-primary-800">
                3
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-surface-900 dark:text-white">Isolation Forest Scoring</h3>
                <p className="text-surface-600 dark:text-surface-400">
                  Fitur-fitur tersebut diumpankan ke model Isolation Forest (Unsupervised Learning). Model ini mencari paket yang secara statistik &quot;terisolasi&quot; dari mayoritas data normal, kemudian menghasilkan skor anomali.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
