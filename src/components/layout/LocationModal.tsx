"use client";

import React, { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { useLocation } from "@/context/LocationContext";
import { MapPin, Navigation } from "lucide-react";

export function LocationModal() {
  const { location, isLocationModalOpen, setIsLocationModalOpen, updateLocation } = useLocation();
  const [pincode, setPincode] = useState(location.pincode);
  const [city, setCity] = useState(location.city);
  const [area, setArea] = useState(location.area);

  const POPULAR_LOCATIONS = [
    { city: "San Francisco", area: "Downtown & Mission", pincode: "94107", time: "12-15 mins" },
    { city: "San Francisco", area: "Sunset & Richmond", pincode: "94122", time: "15-20 mins" },
    { city: "San Jose", area: "Silicon Valley Central", pincode: "95112", time: "15-20 mins" },
    { city: "Oakland", area: "Uptown & Grand Lake", pincode: "94612", time: "18-22 mins" },
  ];

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateLocation({
      city,
      area,
      pincode,
      estimatedDeliveryTime: "15-20 Mins",
    });
    setIsLocationModalOpen(false);
  };

  const selectPreset = (item: (typeof POPULAR_LOCATIONS)[0]) => {
    updateLocation({
      city: item.city,
      area: item.area,
      pincode: item.pincode,
      estimatedDeliveryTime: item.time,
    });
    setIsLocationModalOpen(false);
  };

  return (
    <Modal
      isOpen={isLocationModalOpen}
      onClose={() => setIsLocationModalOpen(false)}
      title="Choose Delivery Location"
      description="Enter your area or postal code to view store availability and exact 15-min delivery slots."
    >
      <form onSubmit={handleSave} className="space-y-4 pt-2">
        <div className="flex gap-2">
          <Input
            label="Postal / Zip Code"
            value={pincode}
            onChange={(e) => setPincode(e.target.value)}
            placeholder="e.g. 94107"
            leftIcon={<MapPin className="w-4 h-4" />}
            required
          />
          <Input
            label="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g. San Francisco"
            required
          />
        </div>

        <Input
          label="Neighborhood / Area"
          value={area}
          onChange={(e) => setArea(e.target.value)}
          placeholder="e.g. Downtown Metro"
          required
        />

        <Button
          type="button"
          variant="secondary"
          size="sm"
          fullWidth
          leftIcon={<Navigation className="w-4 h-4" />}
          onClick={() => {
            setPincode("94107");
            setCity("San Francisco");
            setArea("Financial District & SOMA");
          }}
        >
          Use Current GPS Location
        </Button>

        <div className="pt-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Popular Delivery Hubs
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {POPULAR_LOCATIONS.map((loc) => (
              <button
                type="button"
                key={loc.pincode}
                onClick={() => selectPreset(loc)}
                className="text-left p-2.5 rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/40 transition-all"
              >
                <p className="text-xs font-bold text-slate-800">{loc.area}</p>
                <p className="text-[11px] text-slate-500">{loc.city} ({loc.pincode})</p>
                <span className="inline-block mt-1 text-[10px] font-semibold text-brand-700 bg-brand-100/70 px-1.5 py-0.5 rounded-md">
                  ⚡ {loc.time}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="pt-3 flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => setIsLocationModalOpen(false)}
            fullWidth
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" fullWidth>
            Confirm Location
          </Button>
        </div>
      </form>
    </Modal>
  );
}
