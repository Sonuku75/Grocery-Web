"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { useLocation } from "@/context/LocationContext";
import { useAuth } from "@/context/AuthContext";
import { addressService } from "@/services/addressService";
import { Address } from "@/types";
import { MapPin, Navigation, Home, Building2, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export function LocationModal() {
  const { location, isLocationModalOpen, setIsLocationModalOpen, updateLocation } = useLocation();
  const { isAuthenticated } = useAuth();

  const [pincode, setPincode] = useState(location.pincode || "302001");
  const [city, setCity] = useState(location.city || "Jaipur");
  const [area, setArea] = useState(location.area || "Civil Lines & C-Scheme");
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [savedAddresses, setSavedAddresses] = useState<Address[]>([]);
  const [loadingAddresses, setLoadingAddresses] = useState(false);

  const POPULAR_HUBS = [
    { city: "Jaipur", area: "Civil Lines & C-Scheme", pincode: "302001", time: "10-12 mins" },
    { city: "Jaipur", area: "Malviya Nagar & Jagatpura", pincode: "302017", time: "12-15 mins" },
    { city: "Bengaluru", area: "Indiranagar & Koramangala", pincode: "560038", time: "10-14 mins" },
    { city: "Delhi NCR", area: "Connaught Place & Central", pincode: "110001", time: "12-15 mins" },
    { city: "Mumbai", area: "Bandra & BKC", pincode: "400051", time: "12-15 mins" },
  ];

  // Load saved addresses for authenticated users
  useEffect(() => {
    if (isLocationModalOpen && isAuthenticated) {
      setLoadingAddresses(true);
      addressService
        .getAddresses()
        .then((addrs) => setSavedAddresses(addrs))
        .catch(() => setSavedAddresses([]))
        .finally(() => setLoadingAddresses(false));
    }
  }, [isLocationModalOpen, isAuthenticated]);

  const handleManualSave = (e: React.FormEvent) => {
    e.preventDefault();
    setGeoError(null);

    // Validate 6-digit PIN code
    if (!/^[1-9][0-9]{5}$/.test(pincode.trim())) {
      setGeoError("Please enter a valid 6-digit Indian PIN code (e.g. 302001).");
      return;
    }

    updateLocation({
      city: city.trim(),
      area: area.trim(),
      pincode: pincode.trim(),
      estimatedDeliveryTime: "12-15 Mins",
    });
    setIsLocationModalOpen(false);
  };

  const handleUseCurrentLocation = () => {
    setGeoError(null);
    if (typeof window === "undefined" || !("geolocation" in navigator)) {
      setGeoError("Geolocation is not supported by your web browser. Please enter your location manually.");
      return;
    }

    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGeoLoading(false);
        const { latitude, longitude } = position.coords;
        // Set detected delivery coordinates
        updateLocation({
          city: "Jaipur",
          area: "Current GPS Location",
          pincode: "302001",
          estimatedDeliveryTime: "10-15 Mins",
        });
        setIsLocationModalOpen(false);
      },
      (error) => {
        setGeoLoading(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setGeoError("Location permission denied. Please enter your PIN code or select a saved address.");
            break;
          case error.POSITION_UNAVAILABLE:
            setGeoError("Location information is currently unavailable. Please select your area manually.");
            break;
          case error.TIMEOUT:
            setGeoError("Location request timed out. Please enter your address manually.");
            break;
          default:
            setGeoError("Could not retrieve your location. Please enter manually.");
        }
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  const selectAddress = (addr: Address) => {
    updateLocation({
      city: addr.city,
      area: `${addr.label || addr.addressType || "Saved"}: ${addr.houseFlat || addr.address_line_1}`,
      pincode: addr.pincode || addr.postal_code,
      estimatedDeliveryTime: "10-12 Mins",
    });
    setIsLocationModalOpen(false);
  };

  const selectPreset = (hub: (typeof POPULAR_HUBS)[0]) => {
    updateLocation({
      city: hub.city,
      area: hub.area,
      pincode: hub.pincode,
      estimatedDeliveryTime: hub.time,
    });
    setIsLocationModalOpen(false);
  };

  return (
    <Modal
      isOpen={isLocationModalOpen}
      onClose={() => setIsLocationModalOpen(false)}
      title="Where should we deliver?"
      description="Choose your delivery address or area for accurate 15-minute grocery dispatch."
      maxWidth="lg"
    >
      <div className="space-y-5 pt-2">
        {geoError && (
          <div className="p-3 text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>{geoError}</span>
          </div>
        )}

        {/* Action 1: Geolocation Button */}
        <Button
          type="button"
          variant="secondary"
          size="lg"
          fullWidth
          disabled={geoLoading}
          leftIcon={
            geoLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
            ) : (
              <Navigation className="w-4 h-4 text-brand-600" />
            )
          }
          onClick={handleUseCurrentLocation}
        >
          {geoLoading ? "Detecting GPS Location..." : "Use Current Location (GPS)"}
        </Button>

        {/* Action 2: Saved Delivery Addresses (If user is authenticated) */}
        {isAuthenticated && savedAddresses.length > 0 && (
          <div className="space-y-2">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Your Saved Addresses
            </p>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {savedAddresses.map((addr) => {
                const isDef = addr.isDefault ?? addr.is_default ?? false;
                const isWork = (addr.label || addr.addressType || "").toLowerCase() === "work";
                return (
                  <button
                    key={addr.id}
                    type="button"
                    onClick={() => selectAddress(addr)}
                    className="w-full text-left p-3 rounded-2xl border border-slate-100 hover:border-brand-500 hover:bg-brand-50/20 transition-all flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center group-hover:bg-brand-100 group-hover:text-brand-700 transition-colors">
                        {isWork ? <Building2 className="w-4 h-4" /> : <Home className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">
                            {addr.label || addr.addressType || "Home"}
                          </span>
                          {isDef && (
                            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              Default
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 truncate max-w-[240px] sm:max-w-xs">
                          {addr.houseFlat || addr.address_line_1}, {addr.city} ({addr.pincode || addr.postal_code})
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-brand-600 opacity-0 group-hover:opacity-100 transition-opacity">
                      Deliver Here →
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Action 3: Manual PIN Code & Area Form */}
        <form onSubmit={handleManualSave} className="space-y-3 pt-2 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Or Enter Address Manually
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="City"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. Jaipur"
              required
            />
            <Input
              label="6-Digit PIN Code"
              value={pincode}
              onChange={(e) => setPincode(e.target.value)}
              placeholder="e.g. 302001"
              maxLength={6}
              leftIcon={<MapPin className="w-4 h-4" />}
              required
            />
          </div>

          <Input
            label="Area / Neighborhood"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            placeholder="e.g. Civil Lines, C-Scheme"
            required
          />

          <div className="pt-2 flex gap-2.5">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsLocationModalOpen(false)}
              fullWidth
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" fullWidth>
              Confirm Location
            </Button>
          </div>
        </form>

        {/* Action 4: Popular Delivery Hubs */}
        <div className="pt-2 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            Popular 15-Minute Hubs
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {POPULAR_HUBS.map((hub) => (
              <button
                type="button"
                key={hub.pincode}
                onClick={() => selectPreset(hub)}
                className="text-left p-2.5 rounded-2xl border border-slate-100 hover:border-brand-500 hover:bg-brand-50/30 transition-all group"
              >
                <p className="text-xs font-bold text-slate-800 group-hover:text-brand-600 transition-colors">
                  {hub.area}
                </p>
                <p className="text-[11px] text-slate-500">
                  {hub.city} ({hub.pincode})
                </p>
                <span className="inline-block mt-1 text-[10px] font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200">
                  ⚡ {hub.time}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
