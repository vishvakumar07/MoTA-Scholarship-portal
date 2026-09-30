import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    // Custom breakpoints — content-driven, not generic
    screens: {
      xs:  "375px",   // modern small phones (iPhone SE, Galaxy A series)
      sm:  "640px",   // large phones / small tablets (landscape)
      md:  "768px",   // tablets portrait
      lg:  "1024px",  // tablets landscape / small laptops
      xl:  "1280px",  // desktops
      "2xl": "1536px", // large desktops / 4K
    },
    container: {
      center: true,
      padding: {
        DEFAULT: "1rem",
        sm: "1.5rem",
        lg: "2rem",
      },
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // MoTA brand palette
        mota: {
          navy:       "#0f2042",
          deep:       "#091224",
          blue:       "#1a365d",
          saffron:    "#e67e22",
          gold:       "#d48806",
          green:      "#0d6832",
          lightGreen: "#237804",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      // Fluid spacing tokens
      spacing: {
        "safe-bottom": "env(safe-area-inset-bottom, 0px)",
        "safe-top":    "env(safe-area-inset-top, 0px)",
        "bottom-nav":  "3.5rem",  // 56px — height of mobile bottom nav
      },
      // Fluid min-height for touch targets
      minHeight: {
        touch: "44px",
      },
      minWidth: {
        touch: "44px",
      },
      // Animation for bottom nav + sidebar
      keyframes: {
        "slide-up": {
          from: { transform: "translateY(100%)", opacity: "0" },
          to:   { transform: "translateY(0)",    opacity: "1" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
      },
      animation: {
        "slide-up": "slide-up 0.2s ease-out",
        "fade-in":  "fade-in 0.15s ease-out",
      },
    },
  },
  plugins: [
    // Inline plugin: scrollbar-none utility
    function ({ addUtilities }: any) {
      addUtilities({
        ".scrollbar-none": {
          "-ms-overflow-style": "none",
          "scrollbar-width": "none",
          "&::-webkit-scrollbar": { display: "none" },
        },
        ".scrollbar-thin": {
          "scrollbar-width": "thin",
          "&::-webkit-scrollbar": { width: "6px", height: "6px" },
          "&::-webkit-scrollbar-thumb": { background: "hsl(214.3 31.8% 80%)", "border-radius": "9999px" },
        },
      });
    },
  ],
};

export default config;
