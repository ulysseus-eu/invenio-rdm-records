// This file is part of Invenio-RDM-Records
// Copyright (C) 2020-2023 CERN.
// Copyright (C) 2020-2022 Northwestern University.
//
// Invenio-RDM-Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

/**
 * Traverse the leaves (non-Object, non-Array values) of obj and execute func
 * on each.
 *
 * @param {object} obj - generic Object
 * @param {function} func - (leaf) => ... (identity by default)
 *
 */
export function leafTraverse(obj, func = (l) => l) {
  if (typeof obj === "object") {
    // Objects and Arrays
    for (const key in obj) {
      leafTraverse(obj[key], func);
    }
  } else {
    func(obj);
  }
}

/**
 * Sort a list of string values (options).
 * @param {list} options
 * @returns
 */
export function sortOptions(options) {
  return options.sort((o1, o2) => o1.text.localeCompare(o2.text));
}

/**
 * Scroll page to top
 */
export function scrollTop() {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "smooth",
  });
}

/**
 * Class to handle community types
 */
export class CommunityType {
  constructor(iType = "community") {
    this.communityType = iType;
    this.singulars = {
      person: "person",
      community: "community",
    };
    this.plurals = {
      person: "persons",
      community: "communities",
    };
  }
  getSingular() {
    if (Object.prototype.hasOwnProperty.call(this.singulars, this.communityType)) {
      return this.singulars[this.communityType];
    } else {
      return this.singulars["community"];
    }
  }

  getPlural() {
    if (Object.prototype.hasOwnProperty.call(this.plurals, this.communityType)) {
      return this.plurals[this.communityType];
    } else {
      return this.plurals["community"];
    }
  }

  getSingularCapitalized() {
    return capitalizeFirstLetter(this.getSingular());
  }

  getPluralCapitalized() {
    return capitalizeFirstLetter(this.getPlural());
  }
}

/**
 * Capitalize first letter of string
 */
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}
