"use client";

import React, { ReactNode } from "react";
import { ToastProvider } from "./ToastContext";
import { AuthProvider } from "./AuthContext";
import { CartProvider } from "./CartContext";
import { WishlistProvider } from "./WishlistContext";
import { LocationProvider } from "./LocationContext";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          <WishlistProvider>
            <LocationProvider>{children}</LocationProvider>
          </WishlistProvider>
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
