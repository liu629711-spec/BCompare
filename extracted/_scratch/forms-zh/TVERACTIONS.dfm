object VerActions: TVerActions
  object List: TUiActionList
    object IsSigAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Hint = 'Item Is Important|Marks selected item as important or unimportant.'
    end
    object ShowDetailsAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Text &Details'
      Hint = 'Text Details|Shows or hides text details panel.'
      ImageIndex = imgShowTextDetails
      ShortCaption = 'Details'
      ToolbarAllowed = False
    end
  end
  object Tree: TUiActionTree
    Nodes = ('View: Menu', ('SameModIgnored: MenuItem', 'IsSig: SeparatorItem', 'IsSig: MenuItem', 'OverUnder: MenuItem', 'ShowDetails: MenuItem'), 'Main: Toolbar', ('OverUnder: ToolButton', 'ShowDetails: ToolButton'), 'Edit: PopupMenu', ('Copy: MenuItem', 'N1: SeparatorItem', 'IsSig: MenuItem', 'N2: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem'), 'ExplorerList: SubmenuItem', ()), 'DetailsEdit: PopupMenu', ('Copy: MenuItem'))
  end
end
