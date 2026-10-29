import re
THEMES=[
 ("Journal not formed / wrong", r"jurnal|journal|\bjr_?no\b"),
 ("Camunda / workflow stuck", r"camunda|nyangkut|workflow|subprocess|stuck|tersangkut"),
 ("EOD / EOM / batch / scheduler", r"\beod\b|\beom\b|end of (day|month)|batch|scheduler|cron|\bjob\b|closing"),
 ("Payment / receive / posting / reversal", r"payment|pembayaran|receive|posting|terposting|reversal|autorekon|rekon|\bpp\b|payment point|va\b|virtual account|bayar"),
 ("Prepaid / allocation / pocket / waive / ERT", r"prepaid|alokasi|allocat|pocket|waive|\bert\b|early termination|pelunasan|settlement|refund"),
 ("Disbursement / golive / AP", r"golive|go live|disburs|pencairan|\bap\b|account payable|funding|\bpo\b"),
 ("Status / data sync between systems", r"sinkron|sync|status|cms|db2db|inbound|cdc|tidak sesuai|beda|selisih|mismatch|double|duplikat"),
 ("Login / access / app unavailable", r"login|akses|access|tidak bisa dibuka|blank|loading|down|timeout|time out|lambat|slow|restart|server"),
 ("Integration / third party", r"dukcapil|asliri|privy|esign|e-sign|salesforce|bank|bca|bni|bri|mandiri|api eksternal|vendor|ojk|slik|pefindo|whatsapp|sms|email|otp"),
 ("Calculation / pricing / insurance", r"hitung|calculation|kalkulasi|perhitungan|rate|asuransi|insurance|denda|bunga|interest|pricing|pricelist|tenor|installment|angsuran"),
 ("Document / report / print", r"report|laporan|dokumen|document|cetak|print|pdf|polis|bpkb|kwitansi"),
]
def theme(text):
    t=text.lower()
    for name,p in THEMES:
        if re.search(p,t): return name
    return "Other"
