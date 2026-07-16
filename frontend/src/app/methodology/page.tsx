import { BookOpen, Layers, ShieldCheck, Target } from "lucide-react";

export const metadata = {
  title: 'Metodologi - Dashboard Analitik Pengadaan',
};

export default function MethodologyPage() {
  return (
    <div className="flex-1 bg-surface-50 dark:bg-surface-950 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="mb-12">
          <h1 className="text-3xl font-bold text-surface-900 dark:text-white tracking-tight mb-4 flex items-center gap-3">
            <BookOpen className="h-8 w-8 text-primary-500" />
            Metodologi
          </h1>
          <p className="text-lg text-surface-600 dark:text-surface-400">
            Penjelasan tentang alur data, metode pemeringkatan, dan batas klaim pada sistem ini.
          </p>
        </div>

        {/* Siklus Pengembangan */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white mb-6 flex items-center gap-2">
            <Layers className="h-6 w-6 text-primary-500" />
            Siklus Pengembangan
          </h2>
          <div className="bg-white dark:bg-surface-900 p-6 rounded-2xl border border-surface-200 dark:border-surface-800">
            <p className="text-surface-600 dark:text-surface-400 leading-relaxed mb-4">
              Proyek ini merupakan purwarupa (prototype) analitik berbasis data nyata yang dibangun mengawinkan dua pendekatan terstruktur:
            </p>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <div className="w-8 h-8 rounded bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                  1
                </div>
                <div>
                  <h3 className="font-semibold text-surface-900 dark:text-white mb-1">CRISP-DM (Untuk Pipeline Data)</h3>
                  <p className="text-sm text-surface-600 dark:text-surface-400">
                    Metode standar industri yang memastikan keandalan fase pemahaman data, pembersihan, rekayasa atribut spesifik pengadaan, pemodelan statistik, hingga evaluasi hasil.
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-8 h-8 rounded bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                  2
                </div>
                <div>
                  <h3 className="font-semibold text-surface-900 dark:text-white mb-1">RAD (Untuk Front-End Web)</h3>
                  <p className="text-sm text-surface-600 dark:text-surface-400">
                    Pendekatan pengembangan antarmuka secara iteratif yang difokuskan pada pengalaman pengguna, desain visual yang responsif, dan alur penggunaan yang intuitif.
                  </p>
                </div>
              </li>
            </ul>
          </div>
        </section>

        {/* Pemodelan Isolation Forest */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white mb-6 flex items-center gap-2">
            <Target className="h-6 w-6 text-primary-500" />
            Pemodelan Ketidaklaziman Paket
          </h2>
          <div className="space-y-6">
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="font-bold text-surface-900 dark:text-white mb-3">Mengapa Isolation Forest?</h3>
              <p className="text-surface-600 dark:text-surface-400 text-sm leading-relaxed mb-4">
                Domain pengadaan publik jarang memiliki label pelanggaran yang sudah tervalidasi karena pembuktian substantif membutuhkan pemeriksaan dokumen, klarifikasi, dan proses hukum. Ketiadaan label membatasi penggunaan supervised learning dan metrik klasifikasi. Sistem ini karena itu memakai <strong>Pembelajaran Mesin Tanpa Pengawasan (Unsupervised Machine Learning)</strong>.
              </p>
              <p className="text-surface-600 dark:text-surface-400 text-sm leading-relaxed">
                Algoritma statistik <em>Isolation Forest</em> memetakan pola umum paket tender. Paket dengan kombinasi nilai, waktu, metode, atau riwayat penyedia yang berbeda dari mayoritas data akan memperoleh skor prioritas lebih tinggi.
              </p>
            </div>
          </div>
        </section>

        {/* Rekayasa Fitur */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white mb-6">Aspek Pemeriksaan yang Dihitung</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-surface-900 p-5 rounded-xl border border-surface-200 dark:border-surface-800">
              <h3 className="font-semibold text-surface-900 dark:text-white mb-2">Aspek Waktu</h3>
              <p className="text-sm text-surface-600 dark:text-surface-400">
                Durasi proses tender dihitung untuk melihat paket yang terlalu cepat atau terlalu lama dibandingkan pola umum pada data pembanding.
              </p>
            </div>
            <div className="bg-white dark:bg-surface-900 p-5 rounded-xl border border-surface-200 dark:border-surface-800">
              <h3 className="font-semibold text-surface-900 dark:text-white mb-2">Aspek Keuangan</h3>
              <p className="text-sm text-surface-600 dark:text-surface-400">
                Rasio HPS terhadap pagu dan nilai kontrak terhadap HPS dihitung untuk melihat kedekatan nilai realisasi terhadap batas pembanding anggaran.
              </p>
            </div>
          </div>
        </section>

        {/* Limitasi & Batas Klaim */}
        <section className="mb-12">
          <div className="bg-orange-50 dark:bg-orange-950/20 p-6 rounded-2xl border border-orange-200 dark:border-orange-900/30">
            <h2 className="text-lg font-bold text-orange-800 dark:text-orange-400 mb-4 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              Batas Klaim (Strict Disclaimer)
            </h2>
            <ul className="list-disc pl-5 space-y-3 text-sm text-orange-800 dark:text-orange-300 leading-relaxed">
              <li>
                Sistem ini <strong>TIDAK mendeteksi fraud, korupsi, atau bid-rigging</strong>. Model mesin tidak memiliki kapasitas untuk menuduh intensi kriminal.
              </li>
              <li>
                Sistem murni memetakan <strong>ketidaklaziman statistik</strong> berdasarkan aspek waktu, keuangan, dan konsentrasi penyedia yang berbeda dari distribusi mayoritas tender lain.
              </li>
              <li>
                Daftar Top-N pada tabel <strong>bukan daftar vonis korupsi</strong>, melainkan daftar <strong>prioritas pemeriksaan</strong> yang disarankan untuk ditinjau lebih awal oleh auditor atau analis pengadaan.
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
