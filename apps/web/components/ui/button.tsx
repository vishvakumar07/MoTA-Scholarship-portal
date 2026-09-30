import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/*
  Animation: btn-base class (defined in globals.css) adds:
    - hover: translateY(-1px) + shadow bloom
    - active/press: scale(0.96) — 100ms snap
    - color/border transitions: 200ms ease-out-quart
  All suppressed by prefers-reduced-motion in globals.css.
*/
const buttonVariants = cva(
  [
    "btn-base",                       // ← animation + transitions from globals.css
    "inline-flex items-center justify-center whitespace-nowrap rounded-md",
    "text-sm font-medium",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
    "disabled:pointer-events-none disabled:opacity-50",
    "select-none",                    // prevent text selection on rapid click
  ].join(" "),
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost:
          "hover:bg-accent hover:text-accent-foreground",
        link:
          "text-primary underline-offset-4 hover:underline",
        motaPrimary:
          "bg-blue-900 text-white shadow hover:bg-blue-800 focus-visible:ring-blue-500",
        motaAccent:
          "bg-amber-500 text-white shadow hover:bg-amber-400 focus-visible:ring-amber-400",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm:      "h-8 rounded-md px-3 text-xs",
        lg:      "h-11 rounded-md px-8 text-base",   // bumped to meet 44px touch target
        icon:    "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
