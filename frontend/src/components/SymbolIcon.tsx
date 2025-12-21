interface SymbolIconProps {
  symbol: string;
  size?: number;
}

export const SymbolIcon = ({ symbol, size = 28 }: SymbolIconProps) => {
  const renderSymbol = () => {
    switch (symbol) {
      case 'AAPL':
        // Apple logo - keeping as is (user likes it)
        return (
          <svg viewBox="0 0 24 24" fill="white" width={size} height={size}>
            <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" fill="white"/>
          </svg>
        );
      case 'NVDA':
        // Nvidia - futuristic chip/circuit design
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="nvdaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#76B900" />
                <stop offset="100%" stopColor="#5a9900" />
              </linearGradient>
            </defs>
            <rect x="3" y="3" width="18" height="18" rx="3" stroke="url(#nvdaGrad)" strokeWidth="2" fill="none" />
            <path d="M8 12h8M12 8v8" stroke="url(#nvdaGrad)" strokeWidth="2" strokeLinecap="round" />
            <circle cx="8" cy="8" r="1.5" fill="url(#nvdaGrad)" />
            <circle cx="16" cy="8" r="1.5" fill="url(#nvdaGrad)" />
            <circle cx="8" cy="16" r="1.5" fill="url(#nvdaGrad)" />
            <circle cx="16" cy="16" r="1.5" fill="url(#nvdaGrad)" />
          </svg>
        );
      case 'DXY':
        // Dollar - sleek modern dollar sign
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="dxyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#059669" />
              </linearGradient>
            </defs>
            <path d="M12 3v18M15 7c0-1.66-1.34-3-3-3-1.66 0-3 1.34-3 3s1.34 3 3 3h3c1.66 0 3 1.34 3 3s-1.34 3-3 3c-1.66 0-3-1.34-3-3" stroke="url(#dxyGrad)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
          </svg>
        );
      case 'SPX':
        // S&P 500 - modern geometric S&P
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="spxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#2563eb" />
              </linearGradient>
            </defs>
            <path d="M4 8c0-2.2 1.8-4 4-4h4c2.2 0 4 1.8 4 4s-1.8 4-4 4H8c-2.2 0-4 1.8-4 4s1.8 4 4 4h4c2.2 0 4-1.8 4-4" stroke="url(#spxGrad)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <circle cx="18" cy="12" r="2" fill="url(#spxGrad)" />
          </svg>
        );
      case 'NDQ':
        // NASDAQ - futuristic N with circuit lines
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="ndqGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="100%" stopColor="#7c3aed" />
              </linearGradient>
            </defs>
            <path d="M6 5v14l12-14v14" stroke="url(#ndqGrad)" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="6" cy="5" r="1.5" fill="url(#ndqGrad)" />
            <circle cx="18" cy="19" r="1.5" fill="url(#ndqGrad)" />
          </svg>
        );
      case 'DJI':
        // Dow Jones - sleek D with modern lines
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="djiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#d97706" />
              </linearGradient>
            </defs>
            <path d="M6 5v14h6c4.42 0 8-3.58 8-8s-3.58-6-8-6H6z" stroke="url(#djiGrad)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M14 12h6" stroke="url(#djiGrad)" strokeWidth="2" strokeLinecap="round" opacity="0.6"/>
          </svg>
        );
      case 'VIX':
        // VIX - volatility wave pattern
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="vixGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" />
                <stop offset="100%" stopColor="#dc2626" />
              </linearGradient>
            </defs>
            <path d="M3 12c2-4 4-8 6-4 2 4 4 8 6 4 2-4 4-8 6-4" stroke="url(#vixGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="3" cy="12" r="1.5" fill="url(#vixGrad)" />
            <circle cx="21" cy="8" r="1.5" fill="url(#vixGrad)" />
          </svg>
        );
      case 'MSFT':
        // Microsoft - four squares window logo
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="msftGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#f25022" />
                <stop offset="100%" stopColor="#f97316" />
              </linearGradient>
              <linearGradient id="msftGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#7fba00" />
                <stop offset="100%" stopColor="#84cc16" />
              </linearGradient>
              <linearGradient id="msftGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00a4ef" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
              <linearGradient id="msftGrad4" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#ffb900" />
                <stop offset="100%" stopColor="#fbbf24" />
              </linearGradient>
            </defs>
            <rect x="4" y="4" width="7.5" height="7.5" rx="1" fill="url(#msftGrad1)" />
            <rect x="12.5" y="4" width="7.5" height="7.5" rx="1" fill="url(#msftGrad2)" />
            <rect x="4" y="12.5" width="7.5" height="7.5" rx="1" fill="url(#msftGrad3)" />
            <rect x="12.5" y="12.5" width="7.5" height="7.5" rx="1" fill="url(#msftGrad4)" />
          </svg>
        );
      case 'GOOGL':
        // Google - colorful G
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="googleBlue" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4285f4" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
              <linearGradient id="googleRed" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ea4335" />
                <stop offset="100%" stopColor="#ef4444" />
              </linearGradient>
              <linearGradient id="googleYellow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#fbbc04" />
                <stop offset="100%" stopColor="#fbbf24" />
              </linearGradient>
              <linearGradient id="googleGreen" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#34a853" />
                <stop offset="100%" stopColor="#22c55e" />
              </linearGradient>
            </defs>
            <path d="M12 5c3.87 0 7 3.13 7 7s-3.13 7-7 7-7-3.13-7-7" stroke="url(#googleBlue)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M12 5c-3.87 0-7 3.13-7 7" stroke="url(#googleRed)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M19 12h-7v-2" stroke="url(#googleYellow)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M12 19c3.87 0 7-3.13 7-7" stroke="url(#googleGreen)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
          </svg>
        );
      case 'AMZN':
        // Amazon - smile arrow
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="amznGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff9900" />
                <stop offset="100%" stopColor="#f97316" />
              </linearGradient>
            </defs>
            <path d="M4 14c4 3 8 4 12 4 2 0 4-0.5 4-1" stroke="url(#amznGrad)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
            <path d="M18 17l2-1 1 2" stroke="url(#amznGrad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <text x="12" y="11" textAnchor="middle" fontSize="10" fontWeight="bold" fill="url(#amznGrad)">a</text>
          </svg>
        );
      case 'TSLA':
        // Tesla - stylized T
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="tslaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#e82127" />
                <stop offset="100%" stopColor="#cc0e00" />
              </linearGradient>
            </defs>
            <path d="M6 6h12M12 6v12" stroke="url(#tslaGrad)" strokeWidth="2.8" strokeLinecap="round" fill="none"/>
            <path d="M8 8c0 0 1-2 4-2s4 2 4 2" stroke="url(#tslaGrad)" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
            <circle cx="12" cy="18" r="2" fill="url(#tslaGrad)" />
          </svg>
        );
      case 'META':
        // Meta - infinity symbol
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="metaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0081fb" />
                <stop offset="100%" stopColor="#0668e1" />
              </linearGradient>
            </defs>
            <path d="M6 12c0-3 2-5 4-5s3 2 6 5c3 3 4 5 6 5s4-2 4-5-2-5-4-5-3 2-6 5c-3 3-4 5-6 5s-4-2-4-5z" stroke="url(#metaGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
          </svg>
        );
      case 'AMD':
        // AMD - arrow and chip design
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="amdGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ed1c24" />
                <stop offset="100%" stopColor="#dc2626" />
              </linearGradient>
            </defs>
            <path d="M6 18L18 6M18 6h-8M18 6v8" stroke="url(#amdGrad)" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="6" cy="18" r="2" fill="url(#amdGrad)" />
            <circle cx="18" cy="6" r="2" fill="url(#amdGrad)" />
          </svg>
        );
      case 'NFLX':
        // Netflix - stylized N
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="nflxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#e50914" />
                <stop offset="100%" stopColor="#b20710" />
              </linearGradient>
            </defs>
            <path d="M7 5v14l10-14v14" stroke="url(#nflxGrad)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <path d="M7 5v14" stroke="url(#nflxGrad)" strokeWidth="2" opacity="0.5" strokeLinecap="round"/>
            <path d="M17 5v14" stroke="url(#nflxGrad)" strokeWidth="2" opacity="0.5" strokeLinecap="round"/>
          </svg>
        );
      case 'DIS':
        // Disney - castle silhouette with star
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <defs>
              <linearGradient id="disGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0063e5" />
                <stop offset="100%" stopColor="#3b82f6" />
              </linearGradient>
            </defs>
            <path d="M12 4l-8 8v8h16v-8l-8-8z" stroke="url(#disGrad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <path d="M8 12h8v8H8z" stroke="url(#disGrad)" strokeWidth="1.5" fill="none"/>
            <path d="M12 4v4" stroke="url(#disGrad)" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="12" cy="6" r="1.5" fill="url(#disGrad)" />
          </svg>
        );
      default:
        // Default - clean circular badge with letter
        return (
          <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
            <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="2" opacity="0.5" />
            <text x="12" y="16" textAnchor="middle" fontSize="12" fontWeight="bold" fill="white">
              {symbol.slice(0, 1)}
            </text>
          </svg>
        );
    }
  };

  return <div className="flex items-center justify-center">{renderSymbol()}</div>;
};
