"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createLineItem,
  deleteLineItem,
  fetchLineItems,
  updateLineItem,
  type LineItem,
} from "@/lib/api";

const PAGE_SIZE = 100;

const emptyForm = {
  department: "",
  category: "",
  month: "",
  budget_amount: "",
  actual_amount: "",
  notes: "",
};

function formatCurrency(value: string) {
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n);
}

function formatMonth(value: string) {
  const d = new Date(`${value.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function toMonthInput(value: string) {
  return value.slice(0, 7);
}

export function ScenarioTable({
  scenarioId,
}: {
  scenarioId: number | string;
}) {
  const [items, setItems] = useState<LineItem[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<LineItem | null>(null);
  const [form, setForm] = useState(emptyForm);

  const refresh = useCallback(() => {
    return fetchLineItems(scenarioId, page)
      .then((data) => {
        setItems(data.results);
        setCount(data.count);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error ? err.message : "Failed to load line items"
        );
        setItems([]);
        setCount(0);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [scenarioId, page]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setOpen(true);
  }

  function openEdit(item: LineItem) {
    setEditing(item);
    setForm({
      department: item.department,
      category: item.category,
      month: toMonthInput(item.month),
      budget_amount: item.budget_amount,
      actual_amount: item.actual_amount ?? "",
      notes: item.notes ?? "",
    });
    setOpen(true);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    const payload = {
      scenario: Number(scenarioId),
      department: form.department,
      category: form.category,
      month: `${form.month}-01`,
      budget_amount: form.budget_amount,
      actual_amount: form.actual_amount === "" ? null : form.actual_amount,
      notes: form.notes,
    };
    try {
      if (editing) {
        await updateLineItem(editing.id, payload);
        toast.success("Line item updated");
      } else {
        await createLineItem(payload);
        toast.success("Line item created");
      }
      setOpen(false);
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: LineItem) {
    if (!confirm("Delete this line item?")) return;
    try {
      await deleteLineItem(item.id);
      toast.success("Line item deleted");
      await refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    }
  }

  const start = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, count);
  const hasPrev = page > 1;
  const hasNext = end < count;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium">Line items</h2>
        <Button size="sm" onClick={openCreate}>
          Add line item
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : (
        <>
          <div className="rounded-xl ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Department</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Month</TableHead>
                  <TableHead className="text-right">Budget</TableHead>
                  <TableHead className="text-right">Actual</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-muted-foreground">
                      No line items
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.department}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell>{formatMonth(item.month)}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.budget_amount)}
                      </TableCell>
                      <TableCell className="text-right">
                        {item.actual_amount == null || item.actual_amount === ""
                          ? "—"
                          : formatCurrency(item.actual_amount)}
                      </TableCell>
                      <TableCell className="max-w-[12rem] truncate">
                        {item.notes}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEdit(item)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => void onDelete(item)}
                          >
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
            <span>
              {start}–{end} of {count}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!hasPrev}
                onClick={() => {
                  setLoading(true);
                  setPage((p) => p - 1);
                }}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasNext}
                onClick={() => {
                  setLoading(true);
                  setPage((p) => p + 1);
                }}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <form onSubmit={onSubmit} className="grid gap-4">
            <DialogHeader>
              <DialogTitle>
                {editing ? "Edit line item" : "Add line item"}
              </DialogTitle>
            </DialogHeader>
            <div className="grid gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  required
                  value={form.department}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, department: e.target.value }))
                  }
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="category">Category</Label>
                <Input
                  id="category"
                  required
                  value={form.category}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, category: e.target.value }))
                  }
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="month">Month</Label>
                <Input
                  id="month"
                  type="month"
                  required
                  value={form.month}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, month: e.target.value }))
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="grid gap-1.5">
                  <Label htmlFor="budget">Budget</Label>
                  <Input
                    id="budget"
                    type="number"
                    step="0.01"
                    required
                    value={form.budget_amount}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, budget_amount: e.target.value }))
                    }
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="actual">Actual</Label>
                  <Input
                    id="actual"
                    type="number"
                    step="0.01"
                    value={form.actual_amount}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, actual_amount: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={form.notes}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, notes: e.target.value }))
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
