import { apiClient, isMockMode } from "@/lib/api";
import { Address, AddressInput, AddressListResponse } from "@/types";
import { MOCK_ADDRESSES } from "@/lib/mockData";

const STORAGE_KEY = "cartify_addresses";

function normalizeAddress(raw: any): Address {
  if (!raw) throw new Error("Empty address record");
  const fullName = raw.fullName || raw.recipient_name || raw.recipientName || "Valued Customer";
  const mobile = raw.mobile || raw.phone || "";
  const houseFlat = raw.houseFlat || raw.address_line_1 || raw.addressLine1 || "";
  const street = raw.street || raw.address_line_2 || raw.addressLine2 || "";
  const area = raw.area || raw.address_line_2 || raw.addressLine2 || "";
  const city = raw.city || "";
  const state = raw.state || "";
  const country = raw.country || "India";
  const pincode = raw.pincode || raw.postal_code || raw.postalCode || "";
  const landmark = raw.landmark || undefined;
  const label = raw.label || raw.addressType || "Home";
  const isDefault = raw.isDefault ?? raw.is_default ?? false;
  const latitude = raw.latitude ?? null;
  const longitude = raw.longitude ?? null;
  const createdAt = raw.createdAt || raw.created_at || new Date().toISOString();
  const updatedAt = raw.updatedAt || raw.updated_at || new Date().toISOString();

  return {
    id: String(raw.id),
    userId: raw.userId || raw.user_id,
    user_id: raw.userId || raw.user_id,
    label,
    addressType: (label.toLowerCase() === "work" ? "work" : label.toLowerCase() === "other" ? "other" : "home"),
    recipientName: fullName,
    recipient_name: fullName,
    fullName,
    phone: mobile,
    mobile,
    addressLine1: houseFlat,
    address_line_1: houseFlat,
    houseFlat,
    addressLine2: street,
    address_line_2: street,
    street,
    area,
    landmark,
    city,
    state,
    country,
    postalCode: pincode,
    postal_code: pincode,
    pincode,
    latitude,
    longitude,
    isDefault,
    is_default: isDefault,
    createdAt,
    created_at: createdAt,
    updatedAt,
    updated_at: updatedAt,
  };
}

function toBackendPayload(input: Partial<AddressInput>): Record<string, any> {
  const recipient_name = input.recipientName || input.fullName;
  const phone = input.phone || input.mobile;
  const address_line_1 = input.addressLine1 || input.houseFlat;
  const address_line_2 = input.addressLine2 || input.street || input.area;
  const postal_code = input.postalCode || input.pincode;
  const label = input.label || input.addressType || "Home";
  const is_default = input.isDefault ?? input.is_default;

  const payload: Record<string, any> = {};
  if (recipient_name !== undefined) payload.recipient_name = recipient_name;
  if (phone !== undefined) payload.phone = phone;
  if (address_line_1 !== undefined) payload.address_line_1 = address_line_1;
  if (address_line_2 !== undefined) payload.address_line_2 = address_line_2;
  if (input.landmark !== undefined) payload.landmark = input.landmark;
  if (input.city !== undefined) payload.city = input.city;
  if (input.state !== undefined) payload.state = input.state;
  if (input.country !== undefined) payload.country = input.country;
  if (postal_code !== undefined) payload.postal_code = postal_code;
  if (input.latitude !== undefined) payload.latitude = input.latitude;
  if (input.longitude !== undefined) payload.longitude = input.longitude;
  if (label !== undefined) payload.label = label;
  if (is_default !== undefined) payload.is_default = is_default;

  return payload;
}

export const addressService = {
  getStoredAddresses(): Address[] {
    if (typeof window === "undefined") return MOCK_ADDRESSES.map(normalizeAddress);
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      const initial = MOCK_ADDRESSES.map(normalizeAddress);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(initial));
      return initial;
    }
    try {
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed.map(normalizeAddress) : [];
    } catch {
      return MOCK_ADDRESSES.map(normalizeAddress);
    }
  },

  saveStoredAddresses(addresses: Address[]) {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(addresses));
  },

  async getAddresses(): Promise<Address[]> {
    if (!isMockMode()) {
      const res = await apiClient.get<any>("/addresses");
      if (res.success && res.data) {
        const rawItems = Array.isArray(res.data) ? res.data : res.data.items || [];
        const normalized = rawItems.map(normalizeAddress);
        this.saveStoredAddresses(normalized);
        return normalized;
      }
    }
    return this.getStoredAddresses();
  },

  async getAddress(id: string): Promise<Address | null> {
    if (!isMockMode()) {
      const res = await apiClient.get<any>(`/addresses/${id}`);
      if (res.success && res.data) {
        return normalizeAddress(res.data);
      }
    }
    const all = this.getStoredAddresses();
    return all.find((a) => a.id === id) || null;
  },

  async addAddress(input: AddressInput): Promise<Address> {
    if (!isMockMode()) {
      const payload = toBackendPayload(input);
      const res = await apiClient.post<any>("/addresses", payload);
      if (res.success && res.data) {
        const newAddress = normalizeAddress(res.data);
        const current = this.getStoredAddresses();
        const updated = newAddress.isDefault
          ? [newAddress, ...current.map((a) => ({ ...a, isDefault: false }))]
          : [newAddress, ...current];
        this.saveStoredAddresses(updated);
        return newAddress;
      }
    }

    const current = this.getStoredAddresses();
    const shouldBeDefault = input.isDefault || current.length === 0;
    const newAddress: Address = normalizeAddress({
      ...input,
      id: "addr-" + Date.now(),
      userId: "usr-demo",
      isDefault: shouldBeDefault,
    });

    let updated = [newAddress, ...current];
    if (newAddress.isDefault) {
      updated = updated.map((a) => (a.id === newAddress.id ? a : { ...a, isDefault: false }));
    }
    this.saveStoredAddresses(updated);
    return newAddress;
  },

  async updateAddress(id: string, input: Partial<AddressInput>): Promise<Address> {
    if (!isMockMode()) {
      const payload = toBackendPayload(input);
      const res = await apiClient.patch<any>(`/addresses/${id}`, payload);
      if (res.success && res.data) {
        const updatedAddr = normalizeAddress(res.data);
        const current = this.getStoredAddresses();
        const updated = current.map((a) => (a.id === id ? updatedAddr : (updatedAddr.isDefault ? { ...a, isDefault: false } : a)));
        this.saveStoredAddresses(updated);
        return updatedAddr;
      }
    }

    const current = this.getStoredAddresses();
    let updated = current.map((a) => (a.id === id ? normalizeAddress({ ...a, ...input }) : a));
    if (input.isDefault) {
      updated = updated.map((a) => (a.id === id ? { ...a, isDefault: true } : { ...a, isDefault: false }));
    }
    this.saveStoredAddresses(updated);
    return updated.find((a) => a.id === id)!;
  },

  async deleteAddress(id: string): Promise<boolean> {
    if (!isMockMode()) {
      await apiClient.delete(`/addresses/${id}`);
    }
    const current = this.getStoredAddresses();
    const wasDefault = current.find((a) => a.id === id)?.isDefault;
    let updated = current.filter((a) => a.id !== id);
    if (wasDefault && updated.length > 0) {
      updated[0].isDefault = true;
    }
    this.saveStoredAddresses(updated);
    return true;
  },

  async setDefaultAddress(id: string): Promise<Address[]> {
    if (!isMockMode()) {
      await apiClient.patch(`/addresses/${id}/default`);
    }
    const current = this.getStoredAddresses();
    const updated = current.map((a) => ({ ...a, isDefault: a.id === id }));
    this.saveStoredAddresses(updated);
    return updated;
  },
};
