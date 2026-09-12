"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { Address, AddressInput, AddressType } from "@/types";
import { Home, Building2, MapPin, CheckCircle2 } from "lucide-react";

interface AddressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (addressData: AddressInput) => Promise<void>;
  initialAddress?: Address | null;
}

export function AddressModal({
  isOpen,
  onClose,
  onSave,
  initialAddress,
}: AddressModalProps) {
  const [fullName, setFullName] = useState("");
  const [mobile, setMobile] = useState("");
  const [houseFlat, setHouseFlat] = useState("");
  const [street, setStreet] = useState("");
  const [area, setArea] = useState("");
  const [city, setCity] = useState("Jaipur");
  const [state, setState] = useState("Rajasthan");
  const [country, setCountry] = useState("India");
  const [pincode, setPincode] = useState("302001");
  const [landmark, setLandmark] = useState("");
  const [addressType, setAddressType] = useState<AddressType>("home");
  const [isDefault, setIsDefault] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialAddress) {
      setFullName(initialAddress.fullName || initialAddress.recipient_name || "");
      setMobile(initialAddress.mobile || initialAddress.phone || "");
      setHouseFlat(initialAddress.houseFlat || initialAddress.address_line_1 || "");
      setStreet(initialAddress.street || initialAddress.address_line_2 || "");
      setArea(initialAddress.area || initialAddress.address_line_2 || "");
      setCity(initialAddress.city || "Jaipur");
      setState(initialAddress.state || "Rajasthan");
      setCountry(initialAddress.country || "India");
      setPincode(initialAddress.pincode || initialAddress.postal_code || "302001");
      setLandmark(initialAddress.landmark || "");
      setAddressType(
        initialAddress.addressType ||
          (initialAddress.label?.toLowerCase() === "work" ? "work" : "home")
      );
      setIsDefault(initialAddress.isDefault ?? initialAddress.is_default ?? false);
    } else {
      setFullName("");
      setMobile("");
      setHouseFlat("");
      setStreet("");
      setArea("");
      setCity("Jaipur");
      setState("Rajasthan");
      setCountry("India");
      setPincode("302001");
      setLandmark("");
      setAddressType("home");
      setIsDefault(false);
    }
    setError(null);
  }, [initialAddress, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Indian PIN code validation
    const cleanPin = pincode.trim();
    if (country.toLowerCase() === "india" && !/^[1-9][0-9]{5}$/.test(cleanPin)) {
      setError("Please enter a valid 6-digit Indian PIN code (e.g. 302001).");
      return;
    }

    // Phone validation
    const cleanPhone = mobile.replace(/[\s\-\(\)]/g, "");
    if (!/^(?:\+91|91|0)?[6-9]\d{9}$|^\+?[1-9]\d{7,14}$/.test(cleanPhone)) {
      setError("Please enter a valid 10-digit mobile number (e.g. 9876543210).");
      return;
    }

    setLoading(true);
    try {
      await onSave({
        fullName: fullName.trim(),
        recipientName: fullName.trim(),
        mobile: cleanPhone,
        phone: cleanPhone,
        houseFlat: houseFlat.trim(),
        addressLine1: houseFlat.trim(),
        street: street.trim(),
        area: (area || street).trim(),
        addressLine2: (area || street).trim(),
        city: city.trim(),
        state: state.trim(),
        country: country.trim(),
        pincode: cleanPin,
        postalCode: cleanPin,
        landmark: landmark.trim() || undefined,
        addressType,
        label: addressType === "work" ? "Work" : addressType === "other" ? "Other" : "Home",
        isDefault,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to save address. Please verify your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialAddress ? "Edit Delivery Address" : "Add Delivery Address"}
      description="Enter accurate location details for doorstep 15-minute grocery delivery."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {error && (
          <div className="p-3 text-xs font-medium text-rose-600 bg-rose-50 border border-rose-200 rounded-2xl">
            {error}
          </div>
        )}

        {/* Address Type Pill Selector */}
        <div>
          <label className="block text-[11px] font-bold text-slate-500 mb-1.5 uppercase tracking-wider">
            Address Label
          </label>
          <div className="flex gap-2">
            {[
              { type: "home" as AddressType, label: "Home", icon: Home },
              { type: "work" as AddressType, label: "Work", icon: Building2 },
              { type: "other" as AddressType, label: "Other", icon: MapPin },
            ].map(({ type, label, icon: Icon }) => (
              <button
                key={type}
                type="button"
                onClick={() => setAddressType(type)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  addressType === type
                    ? "bg-brand-600 text-white shadow-xs"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Recipient Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="e.g. Sonu Kumar"
            required
          />
          <Input
            label="Mobile Phone Number"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder="e.g. 9876543210"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Flat / House / Building"
            value={houseFlat}
            onChange={(e) => setHouseFlat(e.target.value)}
            placeholder="e.g. Flat 402, Royal Residency"
            required
          />
          <Input
            label="Street / Road / Locality"
            value={street}
            onChange={(e) => setStreet(e.target.value)}
            placeholder="e.g. Tonk Road, Bapu Nagar"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Input
            label="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g. Jaipur"
            required
          />
          <Input
            label="State"
            value={state}
            onChange={(e) => setState(e.target.value)}
            placeholder="e.g. Rajasthan"
            required
          />
          <Input
            label="6-Digit PIN Code"
            value={pincode}
            onChange={(e) => setPincode(e.target.value)}
            placeholder="e.g. 302001"
            maxLength={6}
            required
          />
        </div>

        <Input
          label="Landmark (Optional)"
          value={landmark}
          onChange={(e) => setLandmark(e.target.value)}
          placeholder="e.g. Near Amar Jawan Jyoti"
        />

        <label className="flex items-center gap-2.5 pt-2 text-xs font-semibold text-slate-700 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={isDefault}
            onChange={(e) => setIsDefault(e.target.checked)}
            className="w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
          />
          <span>Make this my default delivery address</span>
        </label>

        <div className="pt-4 border-t border-slate-100 flex justify-end gap-2.5">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm" isLoading={loading}>
            Save Address
          </Button>
        </div>
      </form>
    </Modal>
  );
}
