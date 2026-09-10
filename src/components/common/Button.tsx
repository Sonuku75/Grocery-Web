"use client";

import React, { forwardRef, ButtonHTMLAttributes, ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98]",
  {
    variants: {
      variant: {
        primary:
          "bg-brand-600 text-white hover:bg-brand-700 shadow-sm hover:shadow active:bg-brand-800",
        secondary:
          "bg-brand-50 text-brand-700 hover:bg-brand-100 active:bg-brand-200 border border-brand-200/60",
        accent:
          "bg-accent-500 text-white hover:bg-accent-600 shadow-sm hover:shadow active:bg-accent-700",
        outline:
          "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 shadow-xs",
        ghost:
          "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
        danger:
          "bg-rose-600 text-white hover:bg-rose-700 shadow-sm active:bg-rose-800",
      },
      size: {
        sm: "text-xs px-3 py-1.5 gap-1.5",
        md: "text-sm px-4 py-2.5 gap-2",
        lg: "text-base px-6 py-3 gap-2.5 font-semibold",
        icon: "h-9 w-9 p-0",
      },
      fullWidth: {
        true: "w-full",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      fullWidth: false,
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      fullWidth,
      isLoading,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(buttonVariants({ variant, size, fullWidth, className }))}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";
