"use client";

import React, { useEffect, useState } from "react";
import { Address, AddressInput } from "@/types";
import { addressService } from "@/services/addressService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { AddressModal } from "@/components/addresses/AddressModal";
import { Plus, Home, Building, Trash2, Edit2, CheckCircle2, MapPin } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function AddressesPage() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    async function load() {
      try {
        const addrs = await addressService.getAddresses();
        setAddresses(addrs);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (data: AddressInput) => {
    if (editingAddress) {
      const updated = await addressService.updateAddress(editingAddress.id, data);
      setAddresses((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
      showToast("Address updated successfully!", "success");
    } else {
      const created = await addressService.addAddress(data);
      setAddresses((prev) => [created, ...prev]);
      showToast("Address saved to address book!", "success");
    }
    setEditingAddress(null);
  };

  const handleDelete = async (id: string) => {
    await addressService.deleteAddress(id);
    setAddresses((prev) => prev.filter((a) => a.id !== id));
    showToast("Address deleted", "info");
  };

  const handleSetDefault = async (id: string) => {
    const updated = await addressService.setDefaultAddress(id);
    setAddresses(updated);
    showToast("Default delivery address updated", "success");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Breadcrumb
        items={[
          { label: "My Profile", href: "/profile" },
          { label: "Saved Addresses" },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-100">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Saved Delivery Addresses
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage your home, apartment, or office locations for quick 1-click checkout.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setEditingAddress(null);
            setIsModalOpen(true);
          }}
        >
          Add New Address
        </Button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading addresses...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {addresses.map((addr) => (
            <div
              key={addr.id}
              className={`p-6 rounded-3xl bg-white border-2 flex flex-col justify-between transition-all shadow-card ${
                addr.isDefault ? "border-brand-500 bg-brand-50/20" : "border-slate-100"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold capitalize text-slate-800 bg-slate-100 px-2.5 py-1 rounded-lg">
                    {addr.addressType === "home" ? (
                      <Home className="w-3.5 h-3.5 text-brand-600" />
                    ) : (
                      <Building className="w-3.5 h-3.5 text-brand-600" />
                    )}
                    {addr.addressType}
                  </span>
                  {addr.isDefault && (
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                      Default Address
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900">{addr.fullName}</h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    {addr.houseFlat}, {addr.street}
                  </p>
                  <p className="text-xs text-slate-600">
                    {addr.area}, {addr.city}, {addr.state} - {addr.pincode}
                  </p>
                  {addr.landmark && (
                    <p className="text-[11px] text-slate-400 mt-1">Landmark: {addr.landmark}</p>
                  )}
                  <p className="text-xs font-mono text-slate-500 mt-2">{addr.mobile}</p>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                {!addr.isDefault && (
                  <button
                    onClick={() => handleSetDefault(addr.id)}
                    className="text-xs font-bold text-brand-600 hover:underline"
                  >
                    Set as Default
                  </button>
                )}
                {addr.isDefault && <div />}

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setEditingAddress(addr);
                      setIsModalOpen(true);
                    }}
                    className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Edit address"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(addr.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Delete address"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <AddressModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingAddress(null);
        }}
        onSave={handleSave}
        initialAddress={editingAddress}
      />
    </div>
  );
}
