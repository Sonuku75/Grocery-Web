"use client";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/common/Modal";
import { Input } from "@/components/common/Input";
import { Button } from "@/components/common/Button";
import { Address, AddressInput, AddressType } from "@/types";

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
  const [city, setCity] = useState("San Francisco");
  const [state, setState] = useState("CA");
  const [pincode, setPincode] = useState("94107");
  const [landmark, setLandmark] = useState("");
  const [addressType, setAddressType] = useState<AddressType>("home");
  const [isDefault, setIsDefault] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialAddress) {
      setFullName(initialAddress.fullName);
      setMobile(initialAddress.mobile);
      setHouseFlat(initialAddress.houseFlat);
      setStreet(initialAddress.street);
      setArea(initialAddress.area);
      setCity(initialAddress.city);
      setState(initialAddress.state);
      setPincode(initialAddress.pincode);
      setLandmark(initialAddress.landmark || "");
      setAddressType(initialAddress.addressType);
      setIsDefault(initialAddress.isDefault);
    } else {
      setFullName("Alex Rivera");
      setMobile("+1 (555) 234-5678");
      setHouseFlat("");
      setStreet("");
      setArea("");
      setCity("San Francisco");
      setState("CA");
      setPincode("94107");
      setLandmark("");
      setAddressType("home");
      setIsDefault(false);
    }
  }, [initialAddress, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave({
        fullName,
        mobile,
        houseFlat,
        street,
        area,
        city,
        state,
        pincode,
        landmark,
        addressType,
        isDefault,
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialAddress ? "Edit Delivery Address" : "Add New Delivery Address"}
      description="Enter your location details for fast 15-minute doorstep dispatch."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Recipient Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <Input
            label="Mobile Number"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Flat / House No. / Building"
            value={houseFlat}
            onChange={(e) => setHouseFlat(e.target.value)}
            placeholder="e.g. Apt 4B, Emerald Heights"
            required
          />
          <Input
            label="Street / Road"
            value={street}
            onChange={(e) => setStreet(e.target.value)}
            placeholder="e.g. 742 Evergreen Terrace"
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Input
            label="Area / Neighborhood"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            placeholder="e.g. Mission District"
            required
          />
          <Input
            label="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
          />
          <Input
            label="Postal / Zip Code"
            value={pincode}
            onChange={(e) => setPincode(e.target.value)}
            required
          />
        </div>

        <Input
          label="Landmark (Optional)"
          value={landmark}
          onChange={(e) => setLandmark(e.target.value)}
          placeholder="e.g. Near Mission Creek Park"
        />

        {/* Address Type */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider">
            Address Type
          </label>
          <div className="flex gap-2">
            {(["home", "work", "other"] as AddressType[]).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setAddressType(type)}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold capitalize transition-all ${
                  addressType === type
                    ? "bg-brand-600 text-white shadow-xs"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 pt-1 text-xs text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={isDefault}
            onChange={(e) => setIsDefault(e.target.checked)}
            className="w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
          />
          <span>Set as my default delivery address</span>
        </label>

        <div className="pt-4 border-t border-slate-100 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={loading}>
            Save Address
          </Button>
        </div>
      </form>
    </Modal>
  );
}
