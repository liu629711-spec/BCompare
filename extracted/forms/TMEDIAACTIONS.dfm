object MediaActions: TMediaActions
  object List: TUiActionList
    object Play2Action: TUiAction
      Category = 'Session'
      Hint = 'Play Both|Plays both audio tracks.'
      ImageIndex = imgMediaPlay2
      ShortCaption = 'Play2'
    end
    object PlayAction: TUiAction
      Category = 'File'
      Hint = 'Play|Plays audio track.'
      ImageIndex = imgMediaPlay
    end
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
    Nodes = ('Session: Menu', ('Info: MenuItem', 'Play2: MenuItem'), 'File: Menu', ('OpenClipboard: MenuItem', 'Play: MenuItem'), 'View: Menu', ('SameModIgnored: MenuItem', 'IsSig: SeparatorItem', 'IsSig: MenuItem', 'OverUnder: MenuItem', 'ShowDetails: MenuItem'), 'Main: Toolbar', ('MergeView: ToolButton', 'Play2: ToolButton', 'OverUnder: ToolButton', 'ShowDetails: ToolButton'), 'Edit: PopupMenu', ('Copy: MenuItem', 'N1: SeparatorItem', 'IsSig: MenuItem', 'N2: SeparatorItem', 'Open: MenuItem', 'OpenLocal: MenuItem', 'OpenProfile: MenuItem', 'Play: MenuItem', 'OpenWithList: SubmenuItem', ('AssocApp: MenuItem', 'RevealInFinder: MenuItem'), 'ExplorerList: SubmenuItem', ()), 'DetailsEdit: PopupMenu', ('Copy: MenuItem'))
  end
end
