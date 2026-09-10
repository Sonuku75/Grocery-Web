"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface DeliveryLocation {
  city: string;
  area: string;
  pincode: string;
  estimatedDeliveryTime: string;
}

interface LocationContextType {
  location: DeliveryLocation;
  isLocationModalOpen: boolean;
  setIsLocationModalOpen: (open: boolean) => void;
  updateLocation: (newLoc: Partial<DeliveryLocation>) => void;
}

const DEFAULT_LOCATION: DeliveryLocation = {
  city: "San Francisco",
  area: "Downtown & Mission",
  pincode: "94107",
  estimatedDeliveryTime: "14 Mins",
};

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export function LocationProvider({ children }: { children: ReactNode }) {
  const [location, setLocation] = useState<DeliveryLocation>(DEFAULT_LOCATION);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("cartify_location");
      if (stored) {
        try {
          setLocation(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const updateLocation = (newLoc: Partial<DeliveryLocation>) => {
    setLocation((prev) => {
      const updated = { ...prev, ...newLoc };
      if (typeof window !== "undefined") {
        localStorage.setItem("cartify_location", JSON.stringify(updated));
      }
      return updated;
    });
  };

  return (
    <LocationContext.Provider
      value={{
        location,
        isLocationModalOpen,
        setIsLocationModalOpen,
        updateLocation,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
}

export function useLocation() {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error("useLocation must be used within a LocationProvider");
  }
  return context;
}
