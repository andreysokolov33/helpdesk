import type { TicketCategoryGroup } from "@/api/ticketCategories";

/** Предзаполнение селектов категория/подкатегория по category_id тикета. */
export function resolveTicketCategorySelection(
  groups: TicketCategoryGroup[],
  categoryId: number | null | undefined,
  categoryParentId: number | null | undefined,
): { parentId: string; childId: string } {
  if (categoryId == null || categoryId <= 0) {
    return { parentId: "", childId: "" };
  }

  if (categoryParentId != null && categoryParentId > 0) {
    const group = groups.find((g) => g.id === categoryParentId);
    if (group?.children.some((c) => c.id === categoryId)) {
      return { parentId: String(categoryParentId), childId: String(categoryId) };
    }
  }

  for (const group of groups) {
    if (group.children.some((c) => c.id === categoryId)) {
      return { parentId: String(group.id), childId: String(categoryId) };
    }
  }

  const asRoot = groups.find((g) => g.id === categoryId);
  if (asRoot) {
    return { parentId: String(categoryId), childId: "" };
  }

  return { parentId: "", childId: "" };
}
