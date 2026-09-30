import React from "react";
import Link from "next/link";
import { ExternalLink, ShieldCheck, Info } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 text-sm border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Col 1: Ministry Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded bg-blue-700 flex items-center justify-center text-white font-bold">
                <ShieldCheck className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h4 className="text-white font-semibold">Ministry of Tribal Affairs</h4>
                <p className="text-xs text-slate-400">Government of India</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-md">
              Official AI-Enabled Digital Platform for Scholarship and Fellowship administration for Scheduled Tribe (ST) students across India. Developed for the Smart India Hackathon.
            </p>
            <div className="flex items-center space-x-2 text-xs text-amber-400/90 bg-amber-950/40 p-2.5 rounded border border-amber-800/40 max-w-md">
              <Info className="w-4 h-4 shrink-0" />
              <span>
                Prototype demonstration system. Data verified against official guidelines on tribal.nic.in.
              </span>
            </div>
          </div>

          {/* Col 2: Official Portals */}
          <div className="space-y-3">
            <h4 className="text-white text-xs font-bold uppercase tracking-wider">
              Official Portals
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://tribal.nic.in/ScholarshiP.aspx"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-400 flex items-center space-x-1"
                >
                  <span>MoTA Scholarship Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://dbttribal.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-400 flex items-center space-x-1"
                >
                  <span>DBT Tribal Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://scholarships.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-400 flex items-center space-x-1"
                >
                  <span>National Scholarship Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://fellowship.tribal.gov.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-400 flex items-center space-x-1"
                >
                  <span>NFST Fellowship Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500" />
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Key Schemes */}
          <div className="space-y-3">
            <h4 className="text-white text-xs font-bold uppercase tracking-wider">
              Administered Schemes
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>Pre-Matric Scholarship (Class IX-X)</li>
              <li>Post-Matric Scholarship</li>
              <li>Top Class Education (265 Institutes)</li>
              <li>National Fellowship (NFST)</li>
              <li>National Overseas Scholarship (NOS)</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-10 pt-6 border-t border-slate-800 text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
          <div>
            © {new Date().getFullYear()} Ministry of Tribal Affairs, Government of India. All rights reserved.
          </div>
          <div className="flex space-x-4">
            <span className="text-slate-400">Security: SHA-256 Aadhaar Hash & AES-256-GCM Bank Encryption</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
