"use client";

import React, { useEffect, useState } from "react";
import { Address, AddressInput } from "@/types";
import { addressService } from "@/services/addressService";
import { Breadcrumb } from "@/components/common/Breadcrumb";
import { Button } from "@/components/common/Button";
import { AddressModal } from "@/components/addresses/AddressModal";
import {
  Plus,
  Home,
  Building2,
  MapPin,
  Trash2,
  Edit3,
  CheckCircle2,
  ShieldCheck,
  Phone,
} from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function AddressesPage() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const { showToast } = useToast();

  const loadAddresses = async () => {
    try {
      const data = await addressService.getAddresses();
      setAddresses(data);
    } catch (err: any) {
      showToast(err?.message || "Failed to load saved addresses.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAddresses();
  }, []);

  const handleSave = async (data: AddressInput) => {
    if (editingAddress) {
      const updated = await addressService.updateAddress(editingAddress.id, data);
      setAddresses((prev) =>
        prev.map((a) => {
          if (a.id === updated.id) return updated;
          if (updated.isDefault) return { ...a, isDefault: false, is_default: false };
          return a;
        })
      );
      showToast("Address updated successfully!", "success");
    } else {
      const created = await addressService.addAddress(data);
      setAddresses((prev) => {
        if (created.isDefault) {
          return [created, ...prev.map((a) => ({ ...a, isDefault: false, is_default: false }))];
        }
        return [created, ...prev];
      });
      showToast("Address added to your address book!", "success");
    }
    setEditingAddress(null);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this delivery address?")) return;
    setActionInProgress(id);
    try {
      await addressService.deleteAddress(id);
      setAddresses((prev) => {
        const remaining = prev.filter((a) => a.id !== id);
        if (remaining.length > 0 && !remaining.some((a) => a.isDefault)) {
          remaining[0].isDefault = true;
          remaining[0].is_default = true;
        }
        return remaining;
      });
      showToast("Address deleted.", "info");
    } catch (err: any) {
      showToast(err?.message || "Failed to delete address.", "error");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    setActionInProgress(id);
    try {
      const updatedList = await addressService.setDefaultAddress(id);
      setAddresses(updatedList);
      showToast("Default delivery address updated.", "success");
    } catch (err: any) {
      showToast(err?.message || "Failed to update default address.", "error");
    } finally {
      setActionInProgress(null);
    }
  };

  const getLabelIcon = (label?: string) => {
    const l = (label || "home").toLowerCase();
    if (l === "work") return <Building2 className="w-3.5 h-3.5 text-brand-600" />;
    if (l === "other") return <MapPin className="w-3.5 h-3.5 text-brand-600" />;
    return <Home className="w-3.5 h-3.5 text-brand-600" />;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <Breadcrumb
        items={[
          { label: "My Profile", href: "/profile" },
          { label: "Saved Addresses" },
        ]}
      />

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Delivery Addresses
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage your saved delivery locations for swift, 15-minute doorstep dispatch.
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

      {/* Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-56 rounded-3xl bg-slate-100 border border-slate-200" />
          ))}
        </div>
      ) : addresses.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 px-4 bg-white rounded-3xl border border-slate-100 shadow-sm max-w-lg mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto shadow-xs">
            <MapPin className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Saved Addresses Found</h3>
          <p className="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
            You haven&apos;t added any delivery addresses yet. Add your home, office, or apartment location to get started.
          </p>
          <div className="pt-2">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => {
                setEditingAddress(null);
                setIsModalOpen(true);
              }}
            >
              Add Your First Address
            </Button>
          </div>
        </div>
      ) : (
        /* Address Cards Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {addresses.map((addr) => {
            const isDef = addr.isDefault ?? addr.is_default ?? false;
            return (
              <div
                key={addr.id}
                className={`p-6 rounded-3xl bg-white border-2 flex flex-col justify-between transition-all duration-200 shadow-card hover:shadow-card-hover ${
                  isDef
                    ? "border-brand-500/80 ring-4 ring-brand-500/10 bg-brand-50/10"
                    : "border-slate-100"
                }`}
              >
                <div className="space-y-3.5">
                  {/* Card Header: Label & Default Badge */}
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 text-xs font-bold capitalize text-slate-800 bg-slate-100/90 px-3 py-1 rounded-xl">
                      {getLabelIcon(addr.label || addr.addressType)}
                      {addr.label || addr.addressType || "Home"}
                    </span>

                    {isDef && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        Default
                      </span>
                    )}
                  </div>

                  {/* Recipient & Address Details */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 leading-snug">
                      {addr.fullName || addr.recipient_name}
                    </h3>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {addr.houseFlat || addr.address_line_1}
                      {(addr.street || addr.address_line_2) && `, ${addr.street || addr.address_line_2}`}
                    </p>

                    <p className="text-xs text-slate-600">
                      {addr.city}, {addr.state} —{" "}
                      <span className="font-semibold text-slate-800">
                        {addr.pincode || addr.postal_code}
                      </span>
                    </p>

                    {addr.landmark && (
                      <p className="text-[11px] text-slate-400 italic pt-0.5">
                        Landmark: {addr.landmark}
                      </p>
                    )}

                    <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 pt-2 font-mono">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{addr.mobile || addr.phone}</span>
                    </div>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                  {!isDef ? (
                    <button
                      onClick={() => handleSetDefault(addr.id)}
                      disabled={actionInProgress === addr.id}
                      className="text-xs font-bold text-brand-600 hover:text-brand-700 hover:underline transition-colors disabled:opacity-50"
                    >
                      Set as Default
                    </button>
                  ) : (
                    <span className="text-[11px] text-slate-400 font-semibold">Primary Address</span>
                  )}

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setEditingAddress(addr);
                        setIsModalOpen(true);
                      }}
                      className="p-2 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
                      title="Edit address"
                      aria-label="Edit address"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(addr.id)}
                      disabled={actionInProgress === addr.id}
                      className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors disabled:opacity-50"
                      title="Delete address"
                      aria-label="Delete address"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Address Edit / Create Modal */}
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
